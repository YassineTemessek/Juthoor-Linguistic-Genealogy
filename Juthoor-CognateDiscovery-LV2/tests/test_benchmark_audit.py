from __future__ import annotations

from pathlib import Path

from juthoor_cognatediscovery_lv2.discovery.benchmark_audit import audit_benchmark_files, audit_benchmark_rows


def test_audit_flags_merger_sensitive_negative() -> None:
    findings = audit_benchmark_rows(
        [
            {
                "source": {"lang": "ara", "lemma": "حمار"},
                "target": {"lang": "arc", "lemma": "חמרא"},
                "relation": "false_friend",
                "notes": "Aramaic ח merges Arabic ح and خ",
            }
        ]
    )
    assert findings
    assert findings[0].finding == "negative_or_false_friend_has_merger_overlap"


def test_audit_flags_merger_sensitive_cognate_as_info() -> None:
    findings = audit_benchmark_rows(
        [
            {
                "source": {"lang": "ara", "lemma": "عين"},
                "target": {"lang": "heb", "lemma": "עין"},
                "relation": "cognate",
            }
        ]
    )
    assert findings
    assert findings[0].severity == "info"


def test_audit_benchmark_files_current_assets() -> None:
    root = Path(__file__).resolve().parents[1] / "resources" / "benchmarks"
    report = audit_benchmark_files([root / "cognate_gold.jsonl", root / "non_cognate_negatives.jsonl"])
    assert report["summary"]["total_findings"] >= 1


def test_modern_coinage_negative_is_not_flagged_for_overlap() -> None:
    findings = audit_benchmark_rows(
        [
            {
                "source": {"lang": "ara", "lemma": "حاسوب"},
                "target": {"lang": "heb", "lemma": "מחשב"},
                "relation": "negative_translation",
                "notes": "Modern coinages for same concept; independently derived",
            }
        ]
    )
    assert findings == []
