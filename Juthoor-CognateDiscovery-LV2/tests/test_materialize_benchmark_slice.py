from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def test_materialize_benchmark_slice_cli(tmp_path: Path):
    benchmark = tmp_path / "benchmark.jsonl"
    source = tmp_path / "source.jsonl"
    target = tmp_path / "target.jsonl"
    out_dir = tmp_path / "out"
    _write_jsonl(
        benchmark,
        [
            {"source": {"lang": "lat", "lemma": "mater"}, "target": {"lang": "grc", "lemma": "μήτηρ"}, "relation": "cognate"},
            {"source": {"lang": "lat", "lemma": "pater"}, "target": {"lang": "grc", "lemma": "πατήρ"}, "relation": "cognate"},
        ],
    )
    _write_jsonl(source, [{"language": "lat", "lemma": "mater"}])
    _write_jsonl(target, [{"language": "grc", "lemma": "μήτηρ"}])

    proc = subprocess.run(
        [
            sys.executable,
            "Juthoor-CognateDiscovery-LV2/scripts/discovery/archive/materialize_benchmark_slice.py",
            "--benchmark",
            str(benchmark),
            "--source",
            f"lat@classical={source}",
            "--target",
            f"grc@ancient={target}",
            "--output-dir",
            str(out_dir),
        ],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["available_pairs"] == 1
    assert (out_dir / "benchmark_lat_grc_available.jsonl").exists()
