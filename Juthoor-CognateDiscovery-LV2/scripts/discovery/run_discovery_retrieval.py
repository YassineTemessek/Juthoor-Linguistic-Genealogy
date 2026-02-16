"""
LV2 discovery-first retrieval using:
- BGE-M3 for multilingual semantic similarity (language-agnostic)
- ByT5 for multilingual form similarity (byte-level, tokenizer-free)

This script generates *ranked leads* for human review.
It does not attempt LV3-style validation.

Prerequisites:
    Run `uv pip install -e .` from the monorepo root to install all packages.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]

# Use proper package imports (requires: uv pip install -e . from monorepo root)
try:
    from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import (
        BgeM3Config,
        BgeM3Embedder,
        ByT5Config,
        ByT5Embedder,
        GeminiConfig,
        GeminiEmbedder,
        estimate_cost,
        estimate_tokens,
    )
    from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import HybridWeights, compute_hybrid
    from juthoor_cognatediscovery_lv2.lv3.discovery.index import FaissIndex, build_flat_ip
    from juthoor_cognatediscovery_lv2.lv3.discovery.jsonl import LexemeRow, read_jsonl_rows, write_jsonl
except ImportError as e:
    raise ImportError(
        f"Failed to import juthoor_cognatediscovery_lv2 package.\n"
        f"Please run 'uv pip install -e .' from the monorepo root directory.\n"
        f"Original error: {e}"
    ) from e


@dataclass(frozen=True)
class CorpusSpec:
    lang: str
    stage: str
    path: Path

    @property
    def label(self) -> str:
        stage = self.stage or "unknown"
        return f"{self.lang}:{stage}"


def parse_spec(value: str) -> CorpusSpec:
    # Format: <lang>[@<stage>]=<path>
    # Examples:
    # - ara@modern=data/processed/arabic/quran_lemmas_enriched.jsonl
    # - eng@old=data/processed/english/english_ipa_merged_pos.jsonl
    if "=" not in value:
        raise ValueError(f"Invalid spec {value!r}. Expected <lang>[@<stage>]=<path>.")
    left, right = value.split("=", 1)
    parts = [p for p in left.split("@") if p != ""]
    if not parts:
        raise ValueError(f"Invalid spec {value!r}: missing <lang>.")
    lang = parts[0]
    stage = parts[1] if len(parts) >= 2 else "unknown"
    return CorpusSpec(lang=lang, stage=stage, path=Path(right))


def _safe_text(text: str) -> str:
    out = " ".join(str(text or "").split()).strip()
    return out if out else ""


def load_lexemes(spec: CorpusSpec, *, limit: int) -> list[LexemeRow]:
    path = spec.path
    if not path.is_absolute():
        path = REPO_ROOT / path
    rows = read_jsonl_rows(path, limit=limit)
    return rows


def cache_paths(*, model: str, spec: CorpusSpec) -> tuple[Path, Path, Path, Path]:
    base = REPO_ROOT / "outputs"
    embeddings_dir = base / "embeddings" / model / spec.lang / (spec.stage or "unknown")
    vectors_path = embeddings_dir / "vectors.npy"
    rows_path = embeddings_dir / "rows.jsonl"

    indexes_dir = base / "indexes" / model / spec.lang / (spec.stage or "unknown")
    index_path = indexes_dir / "index.faiss"
    meta_path = indexes_dir / "meta.json"
    return vectors_path, rows_path, index_path, meta_path


def maybe_load_vectors(vectors_path: Path, rows_path: Path):
    if vectors_path.exists() and rows_path.exists():
        import numpy as np

        vecs = np.load(vectors_path)
        rows = read_jsonl_rows(rows_path, limit=0)
        return vecs, rows
    return None, None


def save_vectors(vectors_path: Path, rows_path: Path, vecs, rows: list[LexemeRow]) -> None:
    import numpy as np

    vectors_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(vectors_path, vecs)
    write_jsonl(rows_path, (r.data | {"_row_idx": r.row_idx} for r in rows))


def embed_corpus(
    *,
    model: str,
    spec: CorpusSpec,
    rows: list[LexemeRow],
    limit: int,
    device: str,
    semantic_cfg: BgeM3Config,
    form_cfg: ByT5Config,
    rebuild_cache: bool,
    backend: str = "local",
):
    # Use a backend-prefixed cache path so local/api vectors don't collide.
    cache_model = f"api_{model}" if backend == "api" else model
    vectors_path, rows_path, _, _ = cache_paths(model=cache_model, spec=spec)
    if not rebuild_cache:
        vecs, cached_rows = maybe_load_vectors(vectors_path, rows_path)
        if vecs is not None and cached_rows is not None:
            return vecs, cached_rows

    texts: list[str] = []
    for r in rows:
        t = _safe_text(r.lemma)
        texts.append(t if t else r.lexeme_id)

    if backend == "api":
        task = "SEMANTIC_SIMILARITY" if model == "semantic" else "RETRIEVAL_DOCUMENT"
        embedder = GeminiEmbedder(config=GeminiConfig(task_type=task, dimensions=1024))
        vecs = embedder.embed(texts)
    elif model == "semantic":
        embedder = BgeM3Embedder(config=semantic_cfg)
        vecs = embedder.embed(texts)
    elif model == "form":
        embedder = ByT5Embedder(config=form_cfg, device=device)
        vecs = embedder.embed(texts)
    else:
        raise ValueError(f"Unknown model {model!r}.")

    save_vectors(vectors_path, rows_path, vecs, rows)
    return vecs, rows


def build_or_load_index(*, model: str, spec: CorpusSpec, vectors, rebuild_index: bool):
    _, _, index_path, meta_path = cache_paths(model=model, spec=spec)
    idx_meta = FaissIndex(index_path=index_path, meta_path=meta_path, dim=int(vectors.shape[1]))

    if not rebuild_index and index_path.exists():
        return idx_meta.load()

    index, dim = build_flat_ip(vectors)
    idx_meta = FaissIndex(index_path=index_path, meta_path=meta_path, dim=dim)
    idx_meta.save(index)
    return index


def search_index(index, query_vectors, topk: int):
    import numpy as np

    topk = int(topk)
    if topk <= 0:
        raise ValueError("topk must be > 0")
    scores, idxs = index.search(np.asarray(query_vectors, dtype="float32"), topk)
    return scores, idxs


def _show_cost_estimate(
    corpora: dict[str, int],
    n_passes: int,
    model_id: str = "gemini-embedding-001",
) -> bool:
    """Print cost estimate table and ask for confirmation. Returns True to proceed."""
    total_texts = sum(corpora.values()) * n_passes
    tokens = estimate_tokens(["word"] * total_texts)  # ~1.2 tokens per lexeme
    cost, is_free = estimate_cost(tokens)

    corpora_str = " + ".join(f"{k} ({v:,})" for k, v in corpora.items())
    cost_str = "FREE (within 3.5M free tier)" if is_free else f"${cost:.4f}"

    print()
    print("+" + "=" * 50 + "+")
    print("|{:^50s}|".format("Gemini API Cost Estimate"))
    print("+" + "=" * 50 + "+")
    print(f"| {'Corpora':<14s}: {corpora_str:<33s}|")
    print(f"| {'Model passes':<14s}: {n_passes:<33d}|")
    print(f"| {'Total texts':<14s}: {total_texts:<33,d}|")
    print(f"| {'Est. tokens':<14s}: {'~' + f'{tokens:,}':<33s}|")
    print(f"| {'Est. cost':<14s}: {cost_str:<33s}|")
    print(f"| {'Model':<14s}: {model_id:<33s}|")
    print("+" + "=" * 50 + "+")
    print()
    return True


@dataclass
class CorpusInfo:
    """Rich metadata about a discovered JSONL corpus file."""
    path: Path
    label: str          # Human-readable name
    language: str       # Language code from JSONL (e.g., "ara-qur", "eng")
    stage: str          # Stage from JSONL (e.g., "Classical", "Modern")
    n_rows: int         # Number of lexeme rows
    group: str          # Display group (e.g., "Arabic", "English")


# ── Language grouping for display ──

_LANG_GROUPS = {
    "ara": "Arabic", "ara-qur": "Arabic",
    "eng": "English",
    "lat": "Latin",
    "grc": "Ancient Greek", "ell": "Greek",
    "heb": "Hebrew",
    "akk": "Akkadian", "uga": "Ugaritic", "gez": "Ge'ez",
    "syr": "Aramaic/Syriac", "syc": "Aramaic/Syriac", "arc": "Aramaic/Syriac",
    "jpa": "Aramaic/Syriac", "tmr": "Aramaic/Syriac",
    "ang": "Old/Middle English", "enm": "Old/Middle English",
}

# ── Filename → human-readable label ──

_LABEL_MAP = {
    "quran_lemmas_enriched": "Quran Lemmas",
    "word_root_map_filtered": "Word-Root Map",
    "hf_roots": "HF Arabic Roots",
    "english_ipa_merged_pos": "English IPA + POS",
    "concepts_v3_2_enriched": "Concepts Index",
}


def _clean_label(stem: str) -> str:
    """Turn a filename stem into a readable label."""
    if stem in _LABEL_MAP:
        return _LABEL_MAP[stem]
    # StarDict pattern: "Latin-English_Wiktionary_dictionary_stardict_filtered"
    s = stem
    for noise in ("_Wiktionary_dictionary_stardict", "_enriched", "_normalized",
                  "_filtered", "-English"):
        s = s.replace(noise, "")
    s = s.replace("_", " ").strip()
    return s if s else stem


def _guess_group(lang_code: str, parent_dir: str) -> str:
    """Map language code or parent directory to a display group."""
    if lang_code in _LANG_GROUPS:
        return _LANG_GROUPS[lang_code]
    # Fallback: guess from parent directory name
    d = parent_dir.lower()
    if "arabic" in d or "arab" in d:
        return "Arabic"
    if "english" in d or "old_english" in d or "middle_english" in d:
        return "English"
    if "latin" in d:
        return "Latin"
    if "greek" in d:
        return "Ancient Greek"
    if "hebrew" in d:
        return "Hebrew"
    if "syriac" in d or "aramaic" in d:
        return "Aramaic/Syriac"
    if "akkadian" in d:
        return "Akkadian"
    if "ugaritic" in d:
        return "Ugaritic"
    if "ge'ez" in d or "geez" in d:
        return "Ge'ez"
    if "hijazi" in d or "gulf" in d or "egyptian" in d or "levantine" in d:
        return "Arabic Dialects"
    return "Other"


def _discover_corpora() -> list[CorpusInfo]:
    """Scan data/processed/ for JSONL files with rich metadata."""
    base = REPO_ROOT / "data" / "processed"
    if not base.exists():
        return []

    results: list[CorpusInfo] = []
    print("  Scanning corpora...", end="", flush=True)
    for p in sorted(base.rglob("*.jsonl")):
        rel = p.relative_to(base)
        parts = rel.parts
        # Skip internal folders
        if any(part.startswith("_") for part in parts):
            continue
        # Skip raw stardict (prefer filtered/normalized/enriched)
        if "raw" in parts:
            continue

        # Read first line for metadata
        language = "unknown"
        stage = "unknown"
        try:
            with open(p, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                if first_line:
                    row = json.loads(first_line)
                    language = row.get("language", "unknown")
                    stage = row.get("stage", "unknown")
        except Exception:
            pass

        # Count lines
        try:
            with open(p, "r", encoding="utf-8") as f:
                n_rows = sum(1 for _ in f)
        except Exception:
            n_rows = 0

        parent_dir = parts[0] if parts else ""
        label = _clean_label(p.stem)
        group = _guess_group(language, parent_dir)

        results.append(CorpusInfo(
            path=p, label=label, language=language,
            stage=stage, n_rows=n_rows, group=group,
        ))
    print(" done.")
    return results


def _interactive_wizard() -> list[str]:
    """Run an interactive wizard and return sys.argv-style args for the parser."""
    print()
    print("=" * 55)
    print("  Juthoor LV2 — Cognate Discovery")
    print("=" * 55)

    # ── Step 1: Backend ──
    print("\n  How do you want to run embeddings?\n")
    print("  1. API   — Gemini cloud, no GPU needed, free tier  [recommended]")
    print("  2. Local — BGE-M3 + ByT5 on your machine (~2GB RAM)")
    choice = input("\n  Choice [1]: ").strip()
    backend = "local" if choice == "2" else "api"

    # ── Discover corpora ──
    corpora = _discover_corpora()
    if not corpora:
        print("\n  No JSONL files found in data/processed/.")
        print("  Run 'ldc ingest --all' first to build canonical datasets.")
        return []

    # Group corpora for display
    from collections import OrderedDict
    groups: dict[str, list[tuple[int, CorpusInfo]]] = OrderedDict()
    # Preferred group order
    for g in ["Arabic", "English", "Latin", "Ancient Greek", "Hebrew",
              "Old/Middle English", "Aramaic/Syriac", "Arabic Dialects",
              "Akkadian", "Ugaritic", "Ge'ez", "Other"]:
        for i, c in enumerate(corpora):
            if c.group == g:
                groups.setdefault(g, []).append((i, c))

    # ── Step 2: Source ──
    print("\n  ── Source (the language you're searching FROM) ──\n")
    for group_name, items in groups.items():
        print(f"  {group_name}:")
        for idx, c in items:
            stage_str = f" ({c.stage})" if c.stage != "unknown" else ""
            print(f"    {idx + 1:3d}. {c.label}{stage_str:<30s} {c.n_rows:>8,d} words")
        print()

    src_input = input("  Source number [1]: ").strip() or "1"
    try:
        src_idx = int(src_input) - 1
        src = corpora[src_idx]
    except (ValueError, IndexError):
        print("  Invalid selection.")
        return []

    # ── Step 3: Targets ──
    print(f"\n  ── Targets (languages to compare '{src.label}' against) ──\n")
    # Re-display without source
    for group_name, items in groups.items():
        filtered = [(i, c) for i, c in items if i != src_idx]
        if not filtered:
            continue
        print(f"  {group_name}:")
        for idx, c in filtered:
            stage_str = f" ({c.stage})" if c.stage != "unknown" else ""
            print(f"    {idx + 1:3d}. {c.label}{stage_str:<30s} {c.n_rows:>8,d} words")
        print()

    tgt_input = input("  Target numbers (comma-separated): ").strip()
    tgt_infos: list[CorpusInfo] = []
    for num in tgt_input.split(","):
        num = num.strip()
        if not num:
            continue
        try:
            idx = int(num) - 1
            if idx == src_idx:
                print(f"    Skipping {num} (same as source)")
                continue
            tgt_infos.append(corpora[idx])
        except (ValueError, IndexError):
            print(f"    Skipping invalid: {num}")

    if not tgt_infos:
        print("  No valid targets selected.")
        return []

    # ── Step 4: Settings (simple) ──
    print("\n  ── Settings ──\n")
    topk_in = input("  Candidates per word [200]: ").strip()
    topk = int(topk_in) if topk_in else 200

    limit_in = input("  Test with small sample? (enter number, or press Enter for all): ").strip()
    limit = int(limit_in) if limit_in else 0

    # ── Step 5: Summary + Cost ──
    models = ["semantic", "form"]
    tgt_summary = " + ".join(f"{c.label} ({c.n_rows:,})" for c in tgt_infos)
    src_stage = src.stage if src.stage != "unknown" else "modern"

    print("\n  ── Summary ──\n")
    print(f"  Source  : {src.label} ({src.n_rows:,} words, {src.stage} {src.language})")
    print(f"  Targets : {tgt_summary}")
    print(f"  Backend : {'Gemini API' if backend == 'api' else 'Local (BGE-M3 + ByT5)'}")
    print(f"  Models  : semantic + form (2 passes)")
    if limit:
        print(f"  Sample  : {limit} words per corpus")

    # Cost estimate for API
    if backend == "api":
        row_counts = {src.label: src.n_rows}
        for c in tgt_infos:
            row_counts[c.label] = c.n_rows
        _show_cost_estimate(row_counts, len(models))

    confirm = input("  Proceed? [Y/n]: ").strip().lower()
    if confirm and confirm != "y":
        print("  Aborted.")
        return []

    # Build argv
    argv = ["--backend", backend]
    argv += ["--source", f"{src.language}@{src_stage}={src.path}"]
    for c in tgt_infos:
        tgt_stage = c.stage if c.stage != "unknown" else "modern"
        argv += ["--target", f"{c.language}@{tgt_stage}={c.path}"]
    argv += ["--models"] + models
    argv += ["--topk", str(topk), "--max-out", str(topk)]
    if limit:
        argv += ["--limit", str(limit)]
    argv += ["--yes"]  # cost already shown

    print("\n  Starting discovery run...\n")
    return argv


def main() -> int:
    # Interactive mode: no args or explicit --interactive
    if len(sys.argv) == 1 or "--interactive" in sys.argv:
        wizard_argv = _interactive_wizard()
        if not wizard_argv:
            return 1
        sys.argv = [sys.argv[0]] + wizard_argv

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="Repeatable. Format: <lang>[@<stage>]=<path>",
    )
    parser.add_argument(
        "--target",
        action="append",
        default=[],
        help="Repeatable. Format: <lang>[@<stage>]=<path>",
    )
    parser.add_argument("--backend", choices=["local", "api"], default="local",
                        help="local = BGE-M3/ByT5 on your machine; api = Gemini embedding-001 via Google API.")
    parser.add_argument("--models", nargs="+", default=["semantic", "form"], choices=["semantic", "form"])
    parser.add_argument("--topk", type=int, default=200, help="Top-K candidates per target corpus (per model).")
    parser.add_argument("--max-out", type=int, default=200, help="Max leads written per source lexeme.")
    parser.add_argument("--limit", type=int, default=0, help="Limit rows loaded per corpus (0 = no limit).")
    parser.add_argument("--device", type=str, default=os.environ.get("LV2_DEVICE", "cpu"))
    parser.add_argument("--rebuild-cache", action="store_true", help="Recompute embeddings even if cached.")
    parser.add_argument("--rebuild-index", action="store_true", help="Rebuild FAISS indexes even if cached.")
    parser.add_argument("--semantic-model", type=str, default="BAAI/bge-m3", help="BGE-M3 model ID.")
    parser.add_argument("--semantic-max-length", type=int, default=8192, help="Max token length for BGE-M3.")
    parser.add_argument("--form-model", type=str, default="google/byt5-small", help="ByT5 model ID.")
    parser.add_argument("--form-pooling", type=str, default="mean", choices=["mean", "cls"])
    parser.add_argument("--no-hybrid", action="store_true", help="Disable heuristic scoring after retrieval.")
    parser.add_argument("--w-semantic", type=float, default=HybridWeights.semantic)
    parser.add_argument("--w-form", type=float, default=HybridWeights.form)
    parser.add_argument("--w-orth", type=float, default=HybridWeights.orthography)
    parser.add_argument("--w-sound", type=float, default=HybridWeights.sound)
    parser.add_argument("--w-skeleton", type=float, default=HybridWeights.skeleton)
    parser.add_argument("--pair-id", type=str, default=None, help="Optional run label (e.g., ara_vs_eng_modern).")
    parser.add_argument("--language-group", type=str, default=None, help="Optional grouping label (e.g., indo_european).")
    parser.add_argument("--output", type=Path, default=None, help="Override output JSONL path.")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip cost confirmation prompt.")
    args = parser.parse_args()

    if args.backend == "api":
        print("[info] Using Gemini embedding-001 API (no local GPU required).")

    if not args.source or not args.target:
        raise SystemExit("Provide at least one --source and one --target.")

    sources = [parse_spec(s) for s in args.source]
    targets = [parse_spec(t) for t in args.target]

    semantic_cfg = BgeM3Config(model_id=args.semantic_model, max_length=args.semantic_max_length)
    form_cfg = ByT5Config(model_id=args.form_model, pooling=args.form_pooling)
    hybrid_weights = HybridWeights(
        semantic=float(args.w_semantic),
        form=float(args.w_form),
        orthography=float(args.w_orth),
        sound=float(args.w_sound),
        skeleton=float(args.w_skeleton),
    )

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = args.output or (REPO_ROOT / "outputs" / "leads" / f"discovery_{run_id}.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # --- Cost estimate (API backend only) ---
    if args.backend == "api":
        # Pre-load row counts for estimate (doesn't load full data yet)
        corpora_counts: dict[str, int] = {}
        for spec in sources + targets:
            path = spec.path if spec.path.is_absolute() else REPO_ROOT / spec.path
            try:
                with open(path, "r", encoding="utf-8") as f:
                    count = sum(1 for _ in f)
            except Exception:
                count = 1000
            corpora_counts[spec.label] = count

        _show_cost_estimate(corpora_counts, len(args.models))
        if not args.yes:
            confirm = input("Proceed? [Y/n]: ").strip().lower()
            if confirm and confirm != "y":
                print("Aborted.")
                return 1

    target_indexes: dict[str, list[tuple[CorpusSpec, Any, list[LexemeRow]]]] = {m: [] for m in args.models}

    for model in args.models:
        for spec in targets:
            rows = load_lexemes(spec, limit=args.limit)
            vecs, cached_rows = embed_corpus(
                model=model,
                spec=spec,
                rows=rows,
                limit=args.limit,
                device=args.device,
                semantic_cfg=semantic_cfg,
                form_cfg=form_cfg,
                rebuild_cache=args.rebuild_cache,
                backend=args.backend,
            )
            cache_model = f"api_{model}" if args.backend == "api" else model
            index = build_or_load_index(model=cache_model, spec=spec, vectors=vecs, rebuild_index=args.rebuild_index)
            target_indexes[model].append((spec, index, cached_rows))

    with out_path.open("w", encoding="utf-8") as out_fh:
        for source_spec in sources:
            source_rows = load_lexemes(source_spec, limit=args.limit)
            # Compute embeddings for the source corpus per model (cached).
            source_vectors_by_model: dict[str, Any] = {}
            source_rows_by_model: dict[str, list[LexemeRow]] = {}
            for model in args.models:
                vecs, cached_rows = embed_corpus(
                    model=model,
                    spec=source_spec,
                    rows=source_rows,
                    limit=args.limit,
                    device=args.device,
                    semantic_cfg=semantic_cfg,
                    form_cfg=form_cfg,
                    rebuild_cache=args.rebuild_cache,
                    backend=args.backend,
                )
                source_vectors_by_model[model] = vecs
                source_rows_by_model[model] = cached_rows

            # Stream results per source lexeme (avoid huge in-memory joins).
            max_out = int(args.max_out)
            topk = int(args.topk)
            for i, src_row in enumerate(source_rows):
                candidates: dict[str, dict[str, Any]] = {}

                for model in args.models:
                    src_vec = source_vectors_by_model[model][i : i + 1]
                    for tgt_spec, tgt_index, tgt_rows in target_indexes[model]:
                        scores, idxs = search_index(tgt_index, src_vec, topk=topk)
                        for score, idx in zip(scores[0].tolist(), idxs[0].tolist(), strict=True):
                            if idx < 0:
                                continue
                            tgt_row = tgt_rows[idx]
                            key = f"{tgt_spec.lang}|{tgt_spec.stage}|{tgt_row.lexeme_id}|{tgt_row.row_idx}"
                            entry = candidates.get(key)
                            if entry is None:
                                entry = {
                                    "run_id": run_id,
                                    "pair_id": args.pair_id,
                                    "language_group": args.language_group,
                                    "source": {
                                        "id": src_row.lexeme_id,
                                        "row_idx": src_row.row_idx,
                                        "lemma": src_row.lemma,
                                        "lang": source_spec.lang,
                                        "stage": source_spec.stage,
                                        "translit": src_row.data.get("translit"),
                                        "ipa": src_row.data.get("ipa") or src_row.data.get("ipa_raw"),
                                        "root_norm": src_row.data.get("root_norm") or src_row.data.get("root"),
                                        "binary_root": src_row.data.get("binary_root"),
                                    },
                                    "target": {
                                        "id": tgt_row.lexeme_id,
                                        "row_idx": tgt_row.row_idx,
                                        "lemma": tgt_row.lemma,
                                        "lang": tgt_spec.lang,
                                        "stage": tgt_spec.stage,
                                        "translit": tgt_row.data.get("translit"),
                                        "ipa": tgt_row.data.get("ipa") or tgt_row.data.get("ipa_raw"),
                                        "root_norm": tgt_row.data.get("root_norm") or tgt_row.data.get("root"),
                                        "binary_root": tgt_row.data.get("binary_root"),
                                    },
                                    "scores": {},
                                    "retrieved_by": [],
                                    "_source_fields": {
                                        "lemma": src_row.data.get("lemma"),
                                        "translit": src_row.data.get("translit"),
                                        "ipa": src_row.data.get("ipa"),
                                        "ipa_raw": src_row.data.get("ipa_raw"),
                                        "root": src_row.data.get("root"),
                                        "root_norm": src_row.data.get("root_norm"),
                                        "binary_root": src_row.data.get("binary_root"),
                                        "binary_root_method": src_row.data.get("binary_root_method"),
                                    },
                                    "_target_fields": {
                                        "lemma": tgt_row.data.get("lemma"),
                                        "translit": tgt_row.data.get("translit"),
                                        "ipa": tgt_row.data.get("ipa"),
                                        "ipa_raw": tgt_row.data.get("ipa_raw"),
                                        "root": tgt_row.data.get("root"),
                                        "root_norm": tgt_row.data.get("root_norm"),
                                        "binary_root": tgt_row.data.get("binary_root"),
                                        "binary_root_method": tgt_row.data.get("binary_root_method"),
                                    },
                                }
                                candidates[key] = entry
                            entry["scores"][model] = float(score)
                            if model not in entry["retrieved_by"]:
                                entry["retrieved_by"].append(model)

                # Category assignment: discovery triage signal (not validation).
                for entry in candidates.values():
                    got_semantic = "semantic" in entry["scores"]
                    got_form = "form" in entry["scores"]
                    if got_semantic and got_form:
                        entry["category"] = "strong_union"
                    elif got_semantic:
                        entry["category"] = "semantic_only"
                    elif got_form:
                        entry["category"] = "form_only"
                    else:
                        entry["category"] = "unclassified"

                    if not args.no_hybrid:
                        entry["hybrid"] = compute_hybrid(
                            source=entry.get("_source_fields", {}),
                            target=entry.get("_target_fields", {}),
                            semantic=entry["scores"].get("semantic"),
                            form=entry["scores"].get("form"),
                            weights=hybrid_weights,
                        )

                    entry["provenance"] = {
                        "lv": "LV2",
                        "mode": "discovery_retrieval",
                        "models": args.models,
                        "topk_per_target": topk,
                        "max_out_per_source": max_out,
                        "pair_id": args.pair_id,
                        "language_group": args.language_group,
                    }

                def sort_key(e: dict[str, Any]):
                    scores = e.get("scores", {})
                    hybrid = e.get("hybrid") or {}
                    combined = hybrid.get("combined_score")
                    return (
                        float(combined) if combined is not None else -1e9,
                        2 if e.get("category") == "strong_union" else 1,
                        float(scores.get("semantic", -1e9)),
                        float(scores.get("form", -1e9)),
                    )

                ranked = sorted(candidates.values(), key=sort_key, reverse=True)[:max_out]
                for row in ranked:
                    row.pop("_source_fields", None)
                    row.pop("_target_fields", None)
                    out_fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Wrote discovery leads: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
