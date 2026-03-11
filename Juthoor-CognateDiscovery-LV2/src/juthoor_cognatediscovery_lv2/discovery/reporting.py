"""
Reporting and output logic for LV2 discovery.
Handles result serialization and HTML report generation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

def write_leads(leads: list[dict[str, Any]], out_path: Path) -> None:
    """
    Writes lead records to a JSONL file.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as out_fh:
        for row in leads:
            out_fh.write(json.dumps(row, ensure_ascii=False) + "\n")

def generate_discovery_report(out_path: Path, script_dir: Path) -> None:
    """
    Attempts to generate an HTML report for a discovery run.
    Uses the co-located report.py script.
    """
    try:
        # Import report generator from scripts/discovery/
        import sys
        if str(script_dir) not in sys.path:
            sys.path.append(str(script_dir))
            
        from report import generate_report
        report_path = out_path.with_suffix(".html")
        generate_report(out_path, report_path)
        print(f"Wrote HTML report:     {report_path}")
    except Exception as exc:
        print(f"[warn] Could not generate HTML report: {exc}")
