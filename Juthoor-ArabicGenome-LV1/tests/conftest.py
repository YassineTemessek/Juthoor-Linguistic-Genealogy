"""
Shared pytest configuration and path helpers for LV1 tests.

Scripts live at Juthoor-ArabicGenome-LV1/scripts/ and are not installed as a
package, so we add the scripts directory to sys.path here so each test module
can import them directly.
"""
import sys
from pathlib import Path

# LV1 root (parent of this tests/ directory)
LV1_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = LV1_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
