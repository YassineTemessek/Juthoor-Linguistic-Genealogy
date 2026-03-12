from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .evaluation import BenchmarkPair, build_metrics, evaluate_pairs, load_benchmark, load_leads


def _norm(value: Any) -> str:
    return " ".join(str(value or "").split()).strip().casefold()


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
        overrides[(_norm(lang), _norm(lemma))] = str(value).strip()
    return overrides


def _benchmark_gloss_map(
    benchmark_pairs: list[BenchmarkPair],
    *,
    side: str,
) -> dict[tuple[str, str], str]:
    glosses: dict[tuple[str, str], str] = {}
    for pair in benchmark_pairs:
        if side == "source":
            key = pair.source_key
            gloss = pair.source_gloss
        else:
            key = pair.target_key
            gloss = pair.target_gloss
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
        lang = _norm(row.get("lang") or row.get("language"))
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
    lang_norm = _norm(lang)
    for pair in benchmark_pairs:
        pair_lang = pair.source_lang if side == "source" else pair.target_lang
        pair_lemma = pair.source_lemma if side == "source" else pair.target_lemma
        if _norm(pair_lang) == lang_norm:
            wanted.add(_norm(pair_lemma))

    seen: set[str] = set()
    subset: list[dict[str, Any]] = []
    for row in corpus_rows:
        lemma = _norm(row.get("lemma"))
        row_lang = _norm(row.get("lang") or row.get("language"))
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
        (_norm(row.get("lang") or row.get("language")), _norm(row.get("lemma")))
        for row in source_rows
    }
    target_keys = {
        (_norm(row.get("lang") or row.get("language")), _norm(row.get("lemma")))
        for row in target_rows
    }

    available: list[dict[str, Any]] = []
    for pair in benchmark_pairs:
        if pair.source_key in source_keys and pair.target_key in target_keys:
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
