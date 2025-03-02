"""
Conftest file for pytest to help find the modules during testing.
"""

import sys
import os
from pathlib import Path

# Add the src directory to path so tests can find the filemaker module
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Add airflow to the sys.modules if not already present
try:
    import airflow
except ImportError:
    # Create a mock airflow module structure
    import types
    airflow = types.ModuleType('airflow')
    providers = types.ModuleType('providers')
    filemaker = types.ModuleType('filemaker')
    
    sys.modules['airflow'] = airflow
    sys.modules['airflow.providers'] = providers
    
    # Create symbolic import path for tests
    from src.airflow.providers import filemaker as fm
    sys.modules['filemaker'] = fm

