from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def test_benchmark_coverage_cli_reports_partial_coverage(tmp_path: Path):
    benchmark = tmp_path / "benchmark.jsonl"
    source = tmp_path / "source.jsonl"
    target = tmp_path / "target.jsonl"
    _write_jsonl(
        benchmark,
        [
            {"source": {"lang": "ara", "lemma": "بيت"}, "target": {"lang": "eng", "lemma": "booth"}, "relation": "cognate"},
            {"source": {"lang": "ara", "lemma": "كلب"}, "target": {"lang": "eng", "lemma": "dog"}, "relation": "negative_translation"},
        ],
    )
    _write_jsonl(source, [{"lang": "ara", "lemma": "بيت"}])
    _write_jsonl(target, [{"lang": "eng", "lemma": "booth"}])

    proc = subprocess.run(
        [
            sys.executable,
            "Juthoor-CognateDiscovery-LV2/scripts/discovery/benchmark_coverage.py",
            "--benchmark",
            str(benchmark),
            "--source",
            f"ara@classical={source}",
            "--target",
            f"eng@modern={target}",
        ],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["covered_pairs"] == 1
    assert payload["missing_pairs"] == 1
