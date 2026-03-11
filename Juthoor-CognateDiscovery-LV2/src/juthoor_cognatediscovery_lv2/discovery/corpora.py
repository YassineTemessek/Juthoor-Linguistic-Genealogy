"""
Corpus discovery and metadata for LV2.
Scans for JSONL lexeme files and provides grouping/labeling logic.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class CorpusSpec:
    lang: str
    stage: str
    path: Path

    @property
    def label(self) -> str:
        stage = self.stage or "unknown"
        return f"{self.lang}:{stage}"

@dataclass
class CorpusInfo:
    """Rich metadata about a discovered JSONL corpus file."""
    path: Path
    label: str          # Human-readable name
    language: str       # Language code from JSONL (e.g., "ara-qur", "eng")
    stage: str          # Stage from JSONL (e.g., "Classical", "Modern")
    n_rows: int         # Number of lexeme rows
    group: str          # Display group (e.g., "Arabic", "English")
    record_type: str = "lexeme"

_LANG_GROUPS = {
    "ara": "Arabic", "ara-qur": "Arabic",
    "eng": "English",
    "lat": "Latin",
    "grc": "Ancient Greek", "ell": "Greek",
    "heb": "Hebrew",
    "akk": "Akkadian", "uga": "Ugaritic", "gez": "Ge'ez",
    "syr": "Aramaic/Syriac", "syc": "Aramaic/Syriac", "arc": "Aramaic/Syriac",
    "jpa": "Aramaic/Syriac", "tmr": "Aramaic/Syriac",
    "aramaic-english": "Aramaic/Syriac",
    "ang": "Old/Middle English", "enm": "Old/Middle English",
}

_STARDICT_RANK = {"enriched": 3, "normalized": 2, "filtered": 1}

_LABEL_MAP = {
    "quran_lemmas_enriched": "Quran Lemmas",
    "word_root_map_filtered": "Word-Root Map",
    "hf_roots": "HF Arabic Roots",
    "english_ipa_merged_pos": "English IPA + POS",
    "concepts_v3_2_enriched": "Concepts Index",
    "arabic_root_families": "Arabic Root Families",
}

def clean_label(stem: str) -> str:
    if stem in _LABEL_MAP:
        return _LABEL_MAP[stem]
    s = stem
    for noise in ("_Wiktionary_dictionary_stardict", "_enriched", "_normalized",
                  "_filtered", "-English"):
        s = s.replace(noise, "")
    s = s.replace("_", " ").strip()
    return s if s else stem

def guess_group(lang_code: str, parent_dir: str, record_type: str = "lexeme") -> str:
    if record_type == "root_family":
        if lang_code == "ara":
            return "Arabic Root Families"
        return "Root Families"
    if lang_code in _LANG_GROUPS:
        return _LANG_GROUPS[lang_code]
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

def discover_corpora(repo_root: Path) -> list[CorpusInfo]:
    raw_results: list[CorpusInfo] = []
    bases = [
        repo_root / "Juthoor-DataCore-LV0" / "data" / "processed",
        repo_root / "data" / "processed",
        repo_root / "Juthoor-CognateDiscovery-LV2" / "outputs" / "corpora",
        repo_root / "outputs" / "corpora",
    ]
    for base in bases:
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.jsonl")):
            rel = p.relative_to(base)
            parts = rel.parts
            if any(part.startswith("_") for part in parts):
                continue
            if "raw" in parts:
                continue

            language = "unknown"
            stage = "unknown"
            record_type = "lexeme"
            try:
                with open(p, "r", encoding="utf-8") as f:
                    first_line = f.readline().strip()
                    if first_line:
                        row = json.loads(first_line)
                        language = row.get("language") or row.get("lang") or "unknown"
                        stage = row.get("stage", "unknown")
                        record_type = row.get("record_type", "lexeme")
            except Exception:
                pass

            try:
                with open(p, "r", encoding="utf-8") as f:
                    n_rows = sum(1 for _ in f)
            except Exception:
                n_rows = 0

            parent_dir = parts[0] if parts else ""
            label = clean_label(p.stem)
            group = guess_group(language, parent_dir, record_type)

            raw_results.append(CorpusInfo(
                path=p, label=label, language=language,
                stage=stage, n_rows=n_rows, group=group, record_type=record_type,
            ))

    best_stardict: dict[str, tuple[int, CorpusInfo]] = {}
    results: list[CorpusInfo] = []
    for c in raw_results:
        if "wiktionary_stardict" in str(c.path):
            variant = c.path.parent.name
            rank = _STARDICT_RANK.get(variant, 0)
            key = c.language
            prev_rank, _ = best_stardict.get(key, (-1, c))
            if rank > prev_rank:
                best_stardict[key] = (rank, c)
        else:
            results.append(c)

    for _, c in sorted(best_stardict.values(), key=lambda x: x[1].label):
        results.append(c)

    return results
