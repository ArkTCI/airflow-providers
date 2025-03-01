#!/usr/bin/env python3
"""
Script to run FileMaker provider unit tests with proper configuration.
This does not require FileMaker credentials.
"""

import os
import sys
import subprocess

# Set up environment variables
os.environ["PYTHONPATH"] = os.path.join(os.getcwd(), "src")

# Run the unit tests
cmd = ["pytest", "tests/unit", "-v"]
print(f"Running unit tests: {' '.join(cmd)}")
result = subprocess.run(cmd)

sys.exit(result.returncode) 