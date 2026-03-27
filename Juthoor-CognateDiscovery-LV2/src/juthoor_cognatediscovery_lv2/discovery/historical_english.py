"""Historical English variant lookup for diachronic cognate matching."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class HistoricalEnglishLookup:
    """Loads Old/Middle English variants for modern English words."""

    def __init__(self, path: Path | str | None = None):
        self._variants: dict[str, dict[str, Any]] = {}
        self._loaded = False
        self._path = path

    def _load(self):
        if self._loaded:
            return
        self._loaded = True
        if self._path is None:
            here = Path(__file__).resolve()
            self._path = (
                here.parents[4]
                / "data"
                / "processed"
                / "english"
                / "historical_variants.jsonl"
            )
        path = Path(self._path)
        if not path.exists():
            return
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                modern = (row.get("modern_lemma") or row.get("lemma", "")).strip().lower()
                if modern:
                    self._variants[modern] = row

    def get_variants(self, modern_lemma: str) -> dict[str, Any] | None:
        """Get Old/Middle English variants for a modern word."""
        self._load()
        return self._variants.get(modern_lemma.strip().lower())

    def has_historical_form(self, modern_lemma: str) -> bool:
        self._load()
        return modern_lemma.strip().lower() in self._variants

    @property
    def size(self) -> int:
        self._load()
        return len(self._variants)
