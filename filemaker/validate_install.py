#!/usr/bin/env python3
"""
Simple script to validate the FileMaker Cloud provider installation.
"""

import importlib
import sys

# Components to test importing
components = [
    "airflow.providers.filemaker",
    "airflow.providers.filemaker.hooks.filemaker",
    "airflow.providers.filemaker.operators.filemaker",
    "airflow.providers.filemaker.sensors.filemaker",
    "airflow.providers.filemaker.auth.cognitoauth",
]

# Additional class names to test
classes = [
    ("airflow.providers.filemaker.hooks.filemaker", "FileMakerHook"),
    ("airflow.providers.filemaker.operators.filemaker", "FileMakerQueryOperator"),
    ("airflow.providers.filemaker.operators.filemaker", "FileMakerExtractOperator"),
    ("airflow.providers.filemaker.operators.filemaker", "FileMakerSchemaOperator"),
    ("airflow.providers.filemaker.sensors.filemaker", "FileMakerDataSensor"),
    ("airflow.providers.filemaker.sensors.filemaker", "FileMakerChangeSensor"),
    ("airflow.providers.filemaker.auth.cognitoauth", "FileMakerCloudAuth"),
]

print("Validating FileMaker Cloud provider installation...")

# Test importing modules
print("\nImporting modules:")
for component in components:
    try:
        module = importlib.import_module(component)
        print(f"  ✅ {component}")
    except ImportError as e:
        print(f"  ❌ {component} - {str(e)}")
        sys.exit(1)

# Test importing classes
print("\nImporting classes:")
for module_name, class_name in classes:
    try:
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        print(f"  ✅ {module_name}.{class_name}")
    except (ImportError, AttributeError) as e:
        print(f"  ❌ {module_name}.{class_name} - {str(e)}")
        sys.exit(1)

# Check for get_provider_info
print("\nChecking provider info:")
try:
    provider_module = importlib.import_module("airflow.providers.filemaker")
    provider_info = provider_module.get_provider_info()
    print(f"  ✅ Provider info found: {provider_info['name']} v{provider_info['versions'][0]}")
except (ImportError, AttributeError, KeyError) as e:
    print(f"  ❌ Provider info not found - {str(e)}")
    sys.exit(1)

print("\n✅ FileMaker Cloud provider validation completed successfully!") 