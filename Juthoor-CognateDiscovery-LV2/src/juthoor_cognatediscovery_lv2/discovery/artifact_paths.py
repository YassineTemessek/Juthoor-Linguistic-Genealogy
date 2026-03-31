from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def lv2_root() -> Path:
    return Path(__file__).resolve().parents[3]


def canonical_outputs_root() -> Path:
    return repo_root() / "outputs"


def lv2_outputs_root() -> Path:
    return lv2_root() / "outputs"


def canonical_cognate_graph_path() -> Path:
    return canonical_outputs_root() / "cognate_graph.json"


def legacy_lv2_cognate_graph_path() -> Path:
    return lv2_outputs_root() / "cognate_graph.json"


def canonical_convergent_leads_path() -> Path:
    return canonical_outputs_root() / "cross_pair_convergent_leads.jsonl"


def legacy_lv2_convergent_leads_path() -> Path:
    return lv2_outputs_root() / "cross_pair_convergent_leads.jsonl"


def resolve_cognate_graph_path(preferred: Path | None = None) -> Path:
    if preferred is not None:
        return preferred

    canonical = canonical_cognate_graph_path()
    if canonical.exists():
        return canonical

    legacy = legacy_lv2_cognate_graph_path()
    if legacy.exists():
        return legacy

    return canonical


def resolve_convergent_leads_path(preferred: Path | None = None) -> Path:
    if preferred is not None:
        return preferred

    canonical = canonical_convergent_leads_path()
    if canonical.exists():
        return canonical

    legacy = legacy_lv2_convergent_leads_path()
    if legacy.exists():
        return legacy

    return canonical
