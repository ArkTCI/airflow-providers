"""
Integration tests for the FileMaker Cloud operators.

These tests require actual FileMaker Cloud credentials to run.
Set the following environment variables to run these tests:
- FILEMAKER_HOST (must include https:// protocol)
- FILEMAKER_DATABASE
- FILEMAKER_USERNAME
- FILEMAKER_PASSWORD
"""

import os
import unittest
from unittest import skipIf

from airflow.models import DAG
from airflow.utils import timezone

from airflow.providers.filemaker.hooks.filemaker import FileMakerHook
from airflow.providers.filemaker.operators.filemaker import FileMakerExtractOperator


@skipIf(
    not all(
        os.environ.get(var)
        for var in ["FILEMAKER_HOST", "FILEMAKER_DATABASE", "FILEMAKER_USERNAME", "FILEMAKER_PASSWORD"]
    ),
    "FileMaker Cloud credentials not available",
)
class TestFileMakerOperators(unittest.TestCase):
    """Integration tests for FileMaker Cloud operators."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.host = os.environ.get("FILEMAKER_HOST")
        cls.database = os.environ.get("FILEMAKER_DATABASE")
        cls.username = os.environ.get("FILEMAKER_USERNAME")
        cls.password = os.environ.get("FILEMAKER_PASSWORD")

        # Set up test DAG
        cls.dag = DAG(
            "test_filemaker_operators",
            default_args={
                "owner": "airflow",
                "start_date": timezone.datetime(2021, 1, 1),
            },
            schedule_interval=None,
        )

        print("\nTesting with:")
        print(f"  Host: {cls.host}")
        print(f"  Database: {cls.database}")
        print(f"  Username: {cls.username}")
        print(f"  Password: {'*' * len(cls.password) if cls.password else None}")

    def test_query_students_table(self):
        """Test FileMakerQueryOperator with _STUDENTS table."""
        print("\nTesting FileMakerQueryOperator with _STUDENTS table...")

        # Create a direct hook instance with credentials
        hook = FileMakerHook(
            host=self.host,
            database=self.database,
            username=self.username,
            password=self.password,
        )

        # Print hook configuration for debugging
        print("Hook configuration:")
        print(f"  Host: {hook.host}")
        print(f"  Database: {hook.database}")
        print(f"  Username: {hook.username}")
        print(f"  Password: {'*' * len(hook.password) if hook.password else None}")

        # Test the hook directly first

        # Get the base URL
        base_url = hook.get_base_url()
        print(f"Base URL: {base_url}")

        # Try to get a token
        token = hook.get_token()
        print(f"Token received: {'Yes' if token else 'No'}")

        # Now try to query the _STUDENTS table directly with the hook
        # Don't use the full URL as the table parameter
        table_name = "_STUDENTS"
        print(f"Querying table: {table_name}")

        # Now try with the operator using JSON format
        print("\nTesting with operator using JSON format...")
        try:
            # Create a new operator with the connection parameters directly
            operator = FileMakerExtractOperator(
                task_id="test_query_students",
                table="_STUDENTS",
                filemaker_conn_id=None,
                hook=hook,  # Don't use a connection ID
                accept_format="application/json",
                output_path="test_output.json",
                format="json",  # Using JSON format
                dag=self.dag,
            )

            # Execute the operator
            result = operator.execute(context={})
            self.assertIsNotNone(result)

            # Print the length of the dictionary and the number of records
            print(f"Query successful with JSON format! Response has {len(result)} top-level keys")
            print(f"Result keys: {list(result.keys())}")
            if isinstance(result, dict) and "value" in result:
                record_count = len(result["value"])
                print(f"Found {record_count} records in the result['value'] array")
                print(f"First record has {len(result['value'][0]) if record_count > 0 else 'N/A'} fields")
                if record_count > 0:
                    # Print some example field names from the first record
                    print(f"Sample fields: {list(result['value'][0].keys())[:5]}")
            else:
                print(f"Result structure: {type(result)}")

        except Exception as e:
            self.fail(f"Direct hook query failed with error: {str(e)}")


if __name__ == "__main__":
    unittest.main()
