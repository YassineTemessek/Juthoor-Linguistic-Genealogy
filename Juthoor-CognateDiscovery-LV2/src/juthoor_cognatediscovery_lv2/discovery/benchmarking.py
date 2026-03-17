from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .evaluation import BenchmarkPair, build_metrics, evaluate_pairs, load_benchmark, load_leads


def _norm(value: Any) -> str:
    return " ".join(str(value or "").split()).strip().casefold()


# ISO 639-1 → ISO 639-3 normalization for benchmark/corpus matching
_LANG_ALIASES: dict[str, str] = {
    "fa": "fas",   # Persian
    "he": "heb",   # Hebrew
    "ar": "ara",   # Arabic
    "en": "eng",   # English
    "la": "lat",   # Latin
    # The following are already ISO 639-3 — keep as identity mappings
    "grc": "grc",  # Ancient Greek
    "arc": "arc",  # Aramaic
    "ang": "ang",  # Old English
    "enm": "enm",  # Middle English
    "fas": "fas",
    "heb": "heb",
    "ara": "ara",
    "eng": "eng",
    "lat": "lat",
}


def _norm_lang(code: str) -> str:
    """Normalize a language code to ISO 639-3 (casefold + alias expansion)."""
    normed = _norm(code)
    return _LANG_ALIASES.get(normed, normed)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def load_gloss_overrides(path: Path) -> dict[tuple[str, str], str]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    overrides: dict[tuple[str, str], str] = {}
    for key, value in payload.items():
        if not value:
            continue
        if ":" in key:
            lang, lemma = key.split(":", 1)
        else:
            lang, lemma = "ara", key
        overrides[(_norm_lang(lang), _norm(lemma))] = str(value).strip()
    return overrides


def _benchmark_gloss_map(
    benchmark_pairs: list[BenchmarkPair],
    *,
    side: str,
) -> dict[tuple[str, str], str]:
    glosses: dict[tuple[str, str], str] = {}
    for pair in benchmark_pairs:
        if side == "source":
            lang = pair.source_lang
            lemma = pair.source_lemma
            gloss = pair.source_gloss
        else:
            lang = pair.target_lang
            lemma = pair.target_lemma
            gloss = pair.target_gloss
        key = (_norm_lang(lang), _norm(lemma))
        if gloss and key not in glosses:
            glosses[key] = gloss
    return glosses


def apply_gloss_overrides(
    rows: list[dict[str, Any]],
    *,
    benchmark_pairs: list[BenchmarkPair],
    side: str,
    overrides: dict[tuple[str, str], str] | None = None,
) -> list[dict[str, Any]]:
    benchmark_glosses = _benchmark_gloss_map(benchmark_pairs, side=side)
    overrides = overrides or {}
    out: list[dict[str, Any]] = []
    for row in rows:
        lang = _norm_lang(row.get("lang") or row.get("language") or "")
        lemma = _norm(row.get("lemma"))
        key = (lang, lemma)
        short_gloss = overrides.get(key) or benchmark_glosses.get(key)
        if short_gloss:
            row = dict(row)
            row["short_gloss"] = short_gloss
        out.append(row)
    return out


def extract_benchmark_subset(
    corpus_rows: list[dict[str, Any]],
    benchmark_pairs: list[BenchmarkPair],
    *,
    lang: str,
    side: str,
    gloss_overrides: dict[tuple[str, str], str] | None = None,
) -> list[dict[str, Any]]:
    if side not in {"source", "target"}:
        raise ValueError("side must be 'source' or 'target'")

    wanted: set[str] = set()
    lang_norm = _norm_lang(lang)
    for pair in benchmark_pairs:
        pair_lang = pair.source_lang if side == "source" else pair.target_lang
        pair_lemma = pair.source_lemma if side == "source" else pair.target_lemma
        if _norm_lang(pair_lang) == lang_norm:
            wanted.add(_norm(pair_lemma))

    seen: set[str] = set()
    subset: list[dict[str, Any]] = []
    for row in corpus_rows:
        lemma = _norm(row.get("lemma"))
        row_lang = _norm_lang(row.get("lang") or row.get("language") or "")
        if lemma in wanted and row_lang == lang_norm and lemma not in seen:
            subset.append(row)
            seen.add(lemma)
    return apply_gloss_overrides(
        subset,
        benchmark_pairs=benchmark_pairs,
        side=side,
        overrides=gloss_overrides,
    )


def filter_available_benchmark_pairs(
    benchmark_pairs: list[BenchmarkPair],
    *,
    source_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source_keys = {
        (_norm_lang(row.get("lang") or row.get("language") or ""), _norm(row.get("lemma")))
        for row in source_rows
    }
    target_keys = {
        (_norm_lang(row.get("lang") or row.get("language") or ""), _norm(row.get("lemma")))
        for row in target_rows
    }

    available: list[dict[str, Any]] = []
    for pair in benchmark_pairs:
        pair_src_key = (_norm_lang(pair.source_lang), _norm(pair.source_lemma))
        pair_tgt_key = (_norm_lang(pair.target_lang), _norm(pair.target_lemma))
        if pair_src_key in source_keys and pair_tgt_key in target_keys:
            available.append(
                {
                    "source": {"lang": pair.source_lang, "lemma": pair.source_lemma},
                    "target": {"lang": pair.target_lang, "lemma": pair.target_lemma},
                    "relation": pair.relation,
                    "confidence": pair.confidence,
                    "notes": pair.notes,
                }
            )
    return available


def build_root_family_benchmark_source(
    source_rows: list[dict[str, Any]],
    root_family_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_root: dict[str, dict[str, Any]] = {}
    by_word: dict[tuple[str, str], dict[str, Any]] = {}
    for row in root_family_rows:
        root = _norm(row.get("root_norm") or row.get("lemma"))
        if root and root not in by_root:
            by_root[root] = row
        lang = _norm(row.get("lang") or row.get("language"))
        for word in row.get("words") or []:
            key = (lang, _norm(word))
            by_word.setdefault(key, row)

    materialized: list[dict[str, Any]] = []
    for row in source_rows:
        row_lang = _norm(row.get("lang") or row.get("language"))
        lemma = _norm(row.get("lemma"))
        root = _norm(row.get("root_norm") or row.get("root"))
        family = by_root.get(root) or by_word.get((row_lang, lemma))
        if not family:
            materialized.append(dict(row))
            continue
        words = [str(item).strip() for item in family.get("words") or [] if str(item).strip()]
        preview = ", ".join(words[:8])
        family_lemma = str(family.get("lemma") or family.get("root_norm") or "").strip()
        form_text = f"{family_lemma} | source: {row.get('lemma')} | words: {preview}" if preview else family_lemma
        meaning_text = str(family.get("meaning_text") or row.get("meaning_text") or row.get("gloss_plain") or "").strip()
        enriched = dict(row)
        enriched.update(
            {
                "id": f"rootfamsrc:{row_lang}:{row.get('lemma')}:{family_lemma}",
                "record_type": "root_family_source",
                "root_family_lemma": family_lemma,
                "words": words,
                "word_count": family.get("word_count", len(words)),
                "form_text": form_text,
                "meaning_text": meaning_text,
                "gloss_plain": str(family.get("gloss_plain") or meaning_text).strip(),
                "binary_root": family.get("binary_root") or row.get("binary_root"),
                "binary_root_meaning": family.get("binary_root_meaning"),
                "axial_meaning": family.get("axial_meaning"),
                "semantic_score": family.get("semantic_score"),
                "short_gloss": row.get("short_gloss") or family.get("short_gloss"),
            }
        )
        materialized.append(enriched)
    return materialized


def evaluate_leads_against_benchmark(leads_path: Path, benchmark_path: Path, *, top_k: int) -> dict[str, Any]:
    benchmark = load_benchmark(benchmark_path)
    leads_by_source = load_leads(leads_path)
    _, metrics = evaluate_pairs(benchmark, leads_by_source, top_k=top_k)
    return metrics


def load_combined_benchmark(paths: list[Path]) -> list[BenchmarkPair]:
    pairs: list[BenchmarkPair] = []
    for path in paths:
        pairs.extend(load_benchmark(path))
    return pairs


def evaluate_leads_against_benchmarks(leads_path: Path, benchmark_paths: list[Path], *, top_k: int) -> dict[str, Any]:
    benchmark = load_combined_benchmark(benchmark_paths)
    leads_by_source = load_leads(leads_path)
    _, metrics = evaluate_pairs(benchmark, leads_by_source, top_k=top_k)
    return metrics


def compare_lead_runs(
    baseline_path: Path,
    candidate_path: Path,
    benchmark_paths: list[Path],
    *,
    top_k: int,
) -> dict[str, Any]:
    baseline = evaluate_leads_against_benchmarks(baseline_path, benchmark_paths, top_k=top_k)
    candidate = evaluate_leads_against_benchmarks(candidate_path, benchmark_paths, top_k=top_k)
    return compare_metrics(baseline, candidate)


def compare_metrics(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    keys = ("recall", "mrr", "ndcg")
    delta = {key: round(float(after.get(key, 0.0)) - float(before.get(key, 0.0)), 6) for key in keys}
    return {
        "baseline": before,
        "reranked": after,
        "delta": delta,
        "improved": any(delta[key] > 0.0 for key in ("mrr", "ndcg", "recall")),
    }
