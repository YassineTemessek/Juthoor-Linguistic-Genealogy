"""
SONAR Embedding CLI - Batch embedding generation using LV2 SonarEmbedder.

This script provides a command-line interface for generating SONAR embeddings
from JSONL files. It delegates to the production SonarEmbedder in LV2.

Prerequisites:
    pip install juthoor-cognatediscovery-lv2[embeddings]

For direct API usage, import from LV2:
    from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import SonarEmbedder

Usage:
    python -m juthoor_datacore_lv0.embeddings.embed_sonar \\
        input.jsonl output_dir/ --lang ara --batch-size 32
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("embed_sonar")

# Check for LV2 availability
_HAS_LV2 = False
_LV2_IMPORT_ERROR = None

try:
    from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import SonarEmbedder, SonarConfig
    from juthoor_cognatediscovery_lv2.lv3.discovery.lang import resolve_sonar_lang
    _HAS_LV2 = True
except ImportError as e:
    _LV2_IMPORT_ERROR = e

try:
    from juthoor_datacore_lv0.ingest.utils import sha256_file
except ImportError:
    # Fallback for running script directly
    def sha256_file(path: Path) -> str:
        import hashlib
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()


def iter_rows(path: Path) -> Iterable[dict]:
    """Iterate over JSONL rows, skipping empty lines."""
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def main() -> int:
    # Check LV2 availability before parsing args
    if not _HAS_LV2:
        logger.error(
            "Missing juthoor_cognatediscovery_lv2 package with embeddings support.\n\n"
            "Install with:\n"
            "    pip install juthoor-cognatediscovery-lv2[embeddings]\n\n"
            "Or install from monorepo:\n"
            "    uv pip install -e Juthoor-CognateDiscovery-LV2\n"
            "    pip install -r Juthoor-CognateDiscovery-LV2/requirements.embeddings.txt"
        )
        if _LV2_IMPORT_ERROR:
            logger.error("Original error: %s", _LV2_IMPORT_ERROR)
        return 1

    ap = argparse.ArgumentParser(
        description="Generate SONAR semantic embeddings for JSONL lexeme files.",
        epilog="Requires: pip install juthoor-cognatediscovery-lv2[embeddings]",
    )
    ap.add_argument("jsonl", type=Path, help="Input JSONL file with meaning_text or lemma fields.")
    ap.add_argument("out_dir", type=Path, help="Output directory for vectors.npy, ids.json, meta.json, coverage.json.")
    ap.add_argument("--lang", type=str, required=True, help="Language code (e.g., ara, eng, heb).")
    ap.add_argument("--sonar-lang", type=str, default=None, help="Override SONAR language code (e.g., arb_Arab).")
    ap.add_argument("--text-field", default="meaning_text", help="Field to embed (default: meaning_text).")
    ap.add_argument("--fallback-field", default="lemma", help="Fallback field if text-field is empty (default: lemma).")
    ap.add_argument("--batch-size", type=int, default=32, help="Batch size for embedding (default: 32).")
    ap.add_argument("--encoder", default="text_sonar_basic_encoder", help="SONAR encoder model.")
    ap.add_argument("--tokenizer", default="text_sonar_basic_encoder", help="SONAR tokenizer model.")
    args = ap.parse_args()

    if not args.jsonl.exists():
        logger.error("Input file not found: %s", args.jsonl)
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)

    # Resolve SONAR language code
    try:
        sonar_lang = resolve_sonar_lang(args.lang, args.sonar_lang)
    except ValueError as e:
        logger.error("%s", e)
        return 1

    logger.info("SONAR language: %s", sonar_lang)
    logger.info("Input: %s", args.jsonl)
    logger.info("Output: %s", args.out_dir)

    # Initialize embedder
    config = SonarConfig(encoder=args.encoder, tokenizer=args.tokenizer)
    embedder = SonarEmbedder(config=config)

    # Collect texts and IDs
    ids: list[str] = []
    texts: list[str] = []
    skipped = 0

    logger.info("Loading rows...")
    for rec in iter_rows(args.jsonl):
        # Get text from primary field or fallback
        text = (rec.get(args.text_field) or "").strip()
        if not text and args.fallback_field:
            text = (rec.get(args.fallback_field) or "").strip()

        vid = rec.get("id") or ""
        if not text or not vid:
            skipped += 1
            continue

        ids.append(vid)
        texts.append(text)

    logger.info("Loaded %d rows, skipped %d", len(texts), skipped)

    if not texts:
        logger.warning("No texts to embed. Writing empty output.")
        mat = np.zeros((0, 1024), dtype="float32")
    else:
        # Batch embedding
        logger.info("Embedding %d texts in batches of %d...", len(texts), args.batch_size)
        all_vecs: list[np.ndarray] = []

        for i in range(0, len(texts), args.batch_size):
            batch = texts[i:i + args.batch_size]
            batch_num = i // args.batch_size + 1
            total_batches = (len(texts) + args.batch_size - 1) // args.batch_size
            logger.debug("Batch %d/%d (%d texts)...", batch_num, total_batches, len(batch))

            vecs = embedder.embed(batch, sonar_lang=sonar_lang)
            all_vecs.append(vecs)

        mat = np.vstack(all_vecs)

    # Write outputs
    logger.info("Writing outputs...")

    (args.out_dir / "ids.json").write_text(
        json.dumps(ids, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    np.save(args.out_dir / "vectors.npy", mat)

    meta = {
        "model_id": args.encoder,
        "tokenizer": args.tokenizer,
        "sonar_lang": sonar_lang,
        "dim": int(mat.shape[1]) if mat.size else 1024,
        "text_field": args.text_field,
        "fallback_field": args.fallback_field,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_jsonl": str(args.jsonl.resolve()),
        "source_sha256": sha256_file(args.jsonl),
        "batch_size": args.batch_size,
    }
    (args.out_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    coverage = {
        "embedded": len(ids),
        "skipped": skipped,
        "total": len(ids) + skipped,
    }
    (args.out_dir / "coverage.json").write_text(
        json.dumps(coverage, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    logger.info("Done! Embedded=%d, skipped=%d, dim=%d", len(ids), skipped, mat.shape[1] if mat.size else 0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
