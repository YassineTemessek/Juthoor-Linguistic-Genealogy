"""
Shared pytest configuration and path helpers for LV1 tests.

Scripts live at Juthoor-ArabicGenome-LV1/scripts/ and are not installed as a
package, so we add the scripts directory to sys.path here so each test module
can import them directly.
"""
import sys
from pathlib import Path
from unittest.mock import patch

# LV1 root (parent of this tests/ directory)
LV1_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = LV1_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# build_genome_phase2.py calls sys.stdout.reconfigure(encoding="utf-8") at
# module level, which can fail when pytest captures stdout with a StringIO
# wrapper that has no reconfigure() method.  We patch it away before the
# module is first imported so the import always succeeds.
if "build_genome_phase2" not in sys.modules:
    with patch("sys.stdout") as _mock_stdout:
        _mock_stdout.reconfigure = lambda **kw: None
        import build_genome_phase2  # noqa: F401 — side-effect import to pre-cache module
