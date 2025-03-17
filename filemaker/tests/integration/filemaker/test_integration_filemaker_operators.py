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

from airflow.providers.filemaker.operators.filemaker import FileMakerQueryOperator
from airflow.providers.filemaker.hooks.filemaker import FileMakerHook


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
        print(f"Hook configuration:")
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

        # Handle JSON or XML response approp
        # Now try with the operator using XML format
        print("\nTesting with operator using XML format...")
        try:
            # Create a new operator with the connection parameters directly
            operator = FileMakerQueryOperator(
                task_id="test_query_students",
                endpoint="_STUDENTS",
                filemaker_conn_id=None,
                hook=hook,  # Don't use a connection ID
                accept_format="application/json",  # Request XML instead of JSON
                dag=self.dag,
            )

            # Execute the operator
            result = operator.execute(context={})
            print("Result: ", result)
            self.assertIsNotNone(result)
            print(f"Operator query successful with XML format! Response length: {len(result)}")

            # Check if we got XML ba
        except Exception as e:
            self.fail(f"Direct hook query failed with error: {str(e)}")


if __name__ == "__main__":
    unittest.main()
