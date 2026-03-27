from __future__ import annotations

import runpy
import sys
from pathlib import Path


if __name__ == "__main__":
    script_path = Path(__file__).resolve().parents[3] / "scripts" / "ingest" / "ingest_kaikki.py"
    script_dir = script_path.parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    runpy.run_path(str(script_path), run_name="__main__")
