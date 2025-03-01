"""
Integration tests for the FileMaker Cloud provider.

These tests require actual FileMaker Cloud credentials to run.
Set the following environment variables to run these tests:
- FILEMAKER_HOST (must include https:// protocol)
- FILEMAKER_DATABASE
- FILEMAKER_USERNAME
- FILEMAKER_PASSWORD
"""
import os
import unittest
import json
from unittest import skipIf

# Try the installed package path first, fall back to direct path for development
from airflow.providers.filemaker.hooks.filemaker import FileMakerHook



@skipIf(
    not all(
        os.environ.get(var)
        for var in ["FILEMAKER_HOST", "FILEMAKER_DATABASE", "FILEMAKER_USERNAME", "FILEMAKER_PASSWORD"]
    ),
    "FileMaker Cloud credentials not available",
)
class TestFileMakerIntegration(unittest.TestCase):
    """Integration tests for FileMaker Cloud provider."""

    def setUp(self):
        """Set up test environment."""
        self.host = os.environ.get("FILEMAKER_HOST")
        self.database = os.environ.get("FILEMAKER_DATABASE")
        self.username = os.environ.get("FILEMAKER_USERNAME")
        self.password = os.environ.get("FILEMAKER_PASSWORD")
        
        print(f"\nTesting with:")
        print(f"  Host: {self.host}")
        print(f"  Database: {self.database}")
        print(f"  Username: {self.username}")
        print(f"  Password: {'*' * len(self.password) if self.password else None}")
        
        self.hook = FileMakerHook(
            host=self.host,
            database=self.database,
            username=self.username,
            password=self.password,
        )

    def test_authentication(self):
        """Test authentication with FileMaker Cloud."""
        try:
            token = self.hook.get_token()
            self.assertIsNotNone(token)
            self.assertTrue(len(token) > 0)
            print(f"\nAuthentication successful. Token prefix: {token[:20]}...")
        except Exception as e:
            self.fail(f"Authentication failed with error: {str(e)}")

    def test_get_base_url(self):
        """Test getting base URL."""
        base_url = self.hook.get_base_url()
        self.assertTrue(base_url.startswith("https://"))
        self.assertTrue("/fmi/odata/v4/" in base_url)
        print(f"\nBase URL constructed correctly: {base_url}")

    def test_get_records(self):
        """Test getting records from a table."""
        # This test assumes there's at least one table in the database
        try:
            # First get metadata to find available tables
            metadata_url = f"{self.hook.get_base_url()}/$metadata"
            print(f"\nFetching metadata from: {metadata_url}")
            metadata = self.hook.get_odata_response(metadata_url, accept_format="application/xml")
            self.assertIsNotNone(metadata)
            print("Metadata retrieved successfully")
            
            # Try to get schema info
            service_root = self.hook.get_base_url()
            print(f"\nFetching service document from: {service_root}")
            service_doc = self.hook.get_odata_response(service_root)
            print(f"Service document: {json.dumps(service_doc, indent=2)[:200]}...")
            
            # If service document has value property with table names, use the first one
            if isinstance(service_doc, dict) and "value" in service_doc and len(service_doc["value"]) > 0:
                # Extract first table name
                first_table = service_doc["value"][0]["name"]
                print(f"\nTesting with first available table: {first_table}")
                
                # Try to get records from this table
                table_url = f"{service_root}/{first_table}"
                print(f"Fetching records from: {table_url}")
                records = self.hook.get_odata_response(table_url)
                self.assertIsNotNone(records)
                print(f"Successfully retrieved records. Response: {json.dumps(records, indent=2)[:200]}...")
                
        except Exception as e:
            self.fail(f"Get records test failed with error: {str(e)}")


if __name__ == "__main__":
    unittest.main() 