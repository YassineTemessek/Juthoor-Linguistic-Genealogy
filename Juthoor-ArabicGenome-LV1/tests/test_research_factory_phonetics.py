from __future__ import annotations

import json
from pathlib import Path


LETTERS = {"ء", "ب", "ت", "ث", "ج", "ح", "خ", "د", "ذ", "ر", "ز", "س", "ش", "ص", "ض", "ط", "ظ", "ع", "غ", "ف", "ق", "ك", "ل", "م", "ن", "ه", "و", "ي"}


def test_phonetic_resources_cover_all_letters():
    base = Path(__file__).resolve().parents[1] / "resources" / "phonetics"
    makhaarij = json.loads((base / "makhaarij.json").read_text(encoding="utf-8"))
    sifaat = json.loads((base / "sifaat.json").read_text(encoding="utf-8"))
    assert set(makhaarij) == LETTERS
    assert set(sifaat) == LETTERS
    assert all("makhraj_id" in rec for rec in makhaarij.values())
    assert all("jahr" in rec for rec in sifaat.values())
