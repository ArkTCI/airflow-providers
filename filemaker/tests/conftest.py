"""
Conftest file for pytest to help find the modules during testing.
"""

import sys
from pathlib import Path

# Add the src directory to path so tests can find the filemaker module
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))
