"""
Conftest file for pytest to help find the modules during testing.
"""
import os
import sys
from pathlib import Path

# Get the root directory of the project
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add the src directory to the path so tests can find the modules
sys.path.insert(0, str(ROOT_DIR / "src"))
