"""Tests for benchmark expansion — validates pair counts, schema, and diversity."""

import json
from pathlib import Path
import pytest

_BENCH = Path(__file__).resolve().parents[1] / "resources" / "benchmarks"
GOLD = _BENCH / "cognate_gold.jsonl"
NEGS = _BENCH / "non_cognate_negatives.jsonl"

REQUIRED_FIELDS = {"source", "target", "relation", "confidence"}
SOURCE_TARGET_FIELDS = {"lang", "lemma"}


def _load(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text("utf-8").splitlines() if l.strip()]


@pytest.fixture(scope="module")
def gold():
    return _load(GOLD)


@pytest.fixture(scope="module")
def negatives():
    return _load(NEGS)


class TestGoldBenchmarkExpansion:
    def test_total_at_least_100(self, gold):
        assert len(gold) >= 100, f"Gold has {len(gold)} pairs, need >= 100"

    def test_arabic_hebrew_at_least_50(self, gold):
        ah = [p for p in gold if p["source"]["lang"] == "ara" and p["target"]["lang"] == "heb"]
        assert len(ah) >= 50, f"Arabic-Hebrew has {len(ah)} pairs, need >= 50"

    def test_arabic_persian_at_least_20(self, gold):
        ap = [p for p in gold if p["source"]["lang"] == "ara" and p["target"]["lang"] == "fa"]
        assert len(ap) >= 20, f"Arabic-Persian has {len(ap)} pairs, need >= 20"

    def test_arabic_aramaic_at_least_15(self, gold):
        aa = [p for p in gold if p["source"]["lang"] == "ara" and p["target"]["lang"] == "arc"]
        assert len(aa) >= 15, f"Arabic-Aramaic has {len(aa)} pairs, need >= 15"

    def test_schema_valid(self, gold):
        for i, p in enumerate(gold):
            missing = REQUIRED_FIELDS - p.keys()
            assert not missing, f"Pair {i} missing: {missing}"
            for side in ("source", "target"):
                side_missing = SOURCE_TARGET_FIELDS - p[side].keys()
                assert not side_missing, f"Pair {i} {side} missing: {side_missing}"

    def test_no_duplicate_pairs(self, gold):
        seen = set()
        for p in gold:
            key = (p["source"]["lang"], p["source"]["lemma"], p["target"]["lang"], p["target"]["lemma"])
            assert key not in seen, f"Duplicate pair: {key}"
            seen.add(key)


class TestNegativeBenchmarkExpansion:
    def test_at_least_30_negatives(self, negatives):
        assert len(negatives) >= 30, f"Negatives has {len(negatives)}, need >= 30"

    def test_has_false_friends(self, negatives):
        ff = [n for n in negatives if n.get("relation") == "false_friend"]
        assert len(ff) >= 5, f"Only {len(ff)} false friends, need >= 5"

    def test_schema_valid(self, negatives):
        for i, n in enumerate(negatives):
            missing = REQUIRED_FIELDS - n.keys()
            assert not missing, f"Negative {i} missing: {missing}"
