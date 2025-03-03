"""
Minimal setup.py for compatibility with older tools.
Most metadata is specified in pyproject.toml.
"""

import setuptools

if __name__ == "__main__":
    setuptools.setup(
        # This minimal setup file is only needed for compatibility with older tools
        # All actual metadata is defined in pyproject.toml
        entry_points={"apache_airflow_provider": ["provider_info=airflow.providers.filemaker:get_provider_info"]},
    )
