"""
CANINE Embedding CLI - Batch embedding generation using LV2 CanineEmbedder.

This script provides a command-line interface for generating CANINE form
embeddings from JSONL files. It delegates to the production CanineEmbedder in LV2.

CANINE is a character-level transformer that can process any Unicode text without
a fixed vocabulary, making it ideal for multilingual form-based similarity.

Prerequisites:
    pip install juthoor-cognatediscovery-lv2[embeddings]

For direct API usage, import from LV2:
    from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import CanineEmbedder

Usage:
    python -m juthoor_datacore_lv0.embeddings.embed_canine \\
        input.jsonl output_dir/ --batch-size 32 --device cpu
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np

# Check for LV2 availability
_HAS_LV2 = False
_LV2_IMPORT_ERROR = None

try:
    from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import CanineEmbedder, CanineConfig
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
        print(
            "ERROR: Missing juthoor_cognatediscovery_lv2 package with embeddings support.\n\n"
            "Install with:\n"
            "    pip install juthoor-cognatediscovery-lv2[embeddings]\n\n"
            "Or install from monorepo:\n"
            "    uv pip install -e Juthoor-CognateDiscovery-LV2\n"
            "    pip install -r Juthoor-CognateDiscovery-LV2/requirements.embeddings.txt\n",
            file=sys.stderr,
        )
        if _LV2_IMPORT_ERROR:
            print(f"Original error: {_LV2_IMPORT_ERROR}", file=sys.stderr)
        return 1

    ap = argparse.ArgumentParser(
        description="Generate CANINE character-level form embeddings for JSONL lexeme files.",
        epilog="Requires: pip install juthoor-cognatediscovery-lv2[embeddings]",
    )
    ap.add_argument("jsonl", type=Path, help="Input JSONL file with form_text or lemma fields.")
    ap.add_argument("out_dir", type=Path, help="Output directory for vectors.npy, ids.json, meta.json, coverage.json.")
    ap.add_argument("--text-field", default="form_text", help="Field to embed (default: form_text).")
    ap.add_argument("--fallback-field", default="lemma", help="Fallback field if text-field is empty (default: lemma).")
    ap.add_argument("--batch-size", type=int, default=32, help="Batch size for embedding (default: 32).")
    ap.add_argument("--device", default="cpu", help="Device for inference: cpu or cuda (default: cpu).")
    ap.add_argument("--model-id", default="google/canine-c", help="CANINE model from HuggingFace.")
    ap.add_argument("--pooling", default="mean", choices=["mean", "cls"], help="Pooling strategy (default: mean).")
    args = ap.parse_args()

    if not args.jsonl.exists():
        print(f"ERROR: Input file not found: {args.jsonl}", file=sys.stderr)
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)

    print(f"CANINE model: {args.model_id}")
    print(f"Pooling: {args.pooling}")
    print(f"Device: {args.device}")
    print(f"Input: {args.jsonl}")
    print(f"Output: {args.out_dir}")

    # Initialize embedder
    config = CanineConfig(model_id=args.model_id, pooling=args.pooling)
    embedder = CanineEmbedder(config=config, device=args.device)

    # Collect texts and IDs
    ids: list[str] = []
    texts: list[str] = []
    skipped = 0

    print("Loading rows...")
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

    print(f"Loaded {len(texts)} rows, skipped {skipped}")

    if not texts:
        print("WARNING: No texts to embed. Writing empty output.")
        mat = np.zeros((0, 768), dtype="float32")  # CANINE hidden size
    else:
        # Batch embedding
        print(f"Embedding {len(texts)} texts in batches of {args.batch_size}...")
        all_vecs: list[np.ndarray] = []

        for i in range(0, len(texts), args.batch_size):
            batch = texts[i:i + args.batch_size]
            batch_num = i // args.batch_size + 1
            total_batches = (len(texts) + args.batch_size - 1) // args.batch_size
            print(f"  Batch {batch_num}/{total_batches} ({len(batch)} texts)...")

            vecs = embedder.embed(batch)
            all_vecs.append(vecs)

        mat = np.vstack(all_vecs)

    # Write outputs
    print("Writing outputs...")

    (args.out_dir / "ids.json").write_text(
        json.dumps(ids, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    np.save(args.out_dir / "vectors.npy", mat)

    meta = {
        "model_id": args.model_id,
        "pooling": args.pooling,
        "device": args.device,
        "dim": int(mat.shape[1]) if mat.size else 768,
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

    print(f"Done! Embedded={len(ids)}, skipped={skipped}, dim={mat.shape[1] if mat.size else 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
