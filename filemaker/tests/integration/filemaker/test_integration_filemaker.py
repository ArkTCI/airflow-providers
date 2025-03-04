"""
Integration tests for the FileMaker Cloud provider.

These tests require actual FileMaker Cloud credentials to run.
Set the following environment variables to run these tests:
- FILEMAKER_HOST (must include https:// protocol)
- FILEMAKER_DATABASE
- FILEMAKER_USERNAME
- FILEMAKER_PASSWORD
"""

import json
import os
import unittest
from unittest import skipIf

import requests
from airflow.models.connection import Connection

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

        print("\nTesting with:")
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
            print("\nAttempting authentication with FileMaker Cloud...")
            print(f"Host: {self.host}")
            print(f"Username: {self.username}")
            print(f"Password length: {len(self.password) if self.password else 0}")

            # Get the hook's auth client directly
            auth_client = self.hook.get_conn()["auth"]
            print(f"Auth client region: {auth_client.region}")
            print(f"Auth client user pool ID: {auth_client.user_pool_id}")
            print(f"Auth client client ID: {auth_client.client_id}")

            # Now try to get the token
            token = self.hook.get_token()
            print(f"Token received: {'Yes' if token else 'No'}")
            print(f"Token length: {len(token) if token else 0}")

            # Validate token format
            if token and len(token) > 20:
                print(f"Token prefix: {token[:20]}...")
                parts = token.split(".")
                print(f"Token has {len(parts)} parts (should be 3 for JWT)")

                if len(parts) == 3:
                    print("Token appears to be a valid JWT format")
                else:
                    print("WARNING: Token does not appear to be in JWT format")

            self.assertIsNotNone(token)
            self.assertTrue(len(token) > 0)
            print("\nAuthentication successful.")
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

            # Get a fresh token first
            token = self.hook.get_token()
            self.assertTrue(token, "Failed to get a valid token")

            # Check token format
            print(f"Using token (first 20 chars): {token[:20]}...")

            # Try a direct request to see what's happening
            headers = {"Authorization": f"FMID {token}", "Accept": "application/xml"}
            print(f"Request headers: {headers}")

            # Make direct request to better diagnose issues
            print("Making direct request with requests library...")
            response = requests.get(metadata_url, headers=headers)
            print(f"Status code: {response.status_code}")
            print(f"Response headers: {response.headers}")

            if response.status_code >= 400:
                print(f"Error response: {response.text[:500]}")

                # Try alternative authentication header formats
                alt_headers = {"Authorization": f"Bearer {token}", "Accept": "application/xml"}
                print("\nTrying with Bearer token instead of FMID...")
                alt_response = requests.get(metadata_url, headers=alt_headers)
                print(f"Status code with Bearer: {alt_response.status_code}")

                if alt_response.status_code < 400:
                    print("Bearer token format works! Consider updating the hook implementation.")

            # Now try with the hook's method
            try:
                metadata = self.hook.get_odata_response(metadata_url, accept_format="application/xml")
                self.assertIsNotNone(metadata)
                print("Metadata retrieved successfully")
            except Exception as e:
                print(f"Hook's get_odata_response failed: {str(e)}")
                print("Continuing with test to gather more diagnostic info...")

            # Try to get schema info
            service_root = self.hook.get_base_url()
            print(f"\nFetching service document from: {service_root}")

            try:
                service_doc = self.hook.get_odata_response(service_root)
                print(f"Service document retrieved: {type(service_doc)}")
                if isinstance(service_doc, dict):
                    print(f"Keys in service document: {service_doc.keys()}")

                    # If service document has value property with table names, use the first one
                    if "value" in service_doc and len(service_doc["value"]) > 0:
                        first_table = service_doc["value"][0]["name"]
                        print(f"\nTesting with first available table: {first_table}")

                        # Try to get records from this table
                        table_url = f"{service_root}/{first_table}"
                        print(f"Fetching records from: {table_url}")
                        records = self.hook.get_odata_response(table_url)
                        self.assertIsNotNone(records)
                        print(f"Successfully retrieved records. Response: {json.dumps(records, indent=2)[:200]}...")
                else:
                    print(f"Service document content: {service_doc}")
            except Exception as e:
                print(f"Error accessing service document: {str(e)}")
                raise  # Re-raise to fail the test

        except Exception as e:
            self.fail(f"Get records test failed with error: {str(e)}")

    def test_connection_test_method(self):
        """Test the test_connection method with real credentials."""
        print("\nTesting the test_connection method with real credentials...")

        # Create a test connection with real credentials
        conn = Connection(
            conn_id="test_filemaker_conn",
            conn_type="filemaker",
            host=self.host,
            schema=self.database,
            login=self.username,
            password=self.password,
        )

        # Test the connection
        status, message = FileMakerHook.test_connection(conn)
        self.assertTrue(status, f"Connection test failed: {message}")
        print(f"Connection test succeeded with message: {message}")

    def test_request_data_methods(self):
        """Test the comprehensive set of OData request data methods."""
        print("\nTesting all OData request data methods...")

        try:
            # 1. First get service document to find available tables
            service_root = self.hook.get_base_url()
            print(f"Fetching service document from: {service_root}")

            service_doc = self.hook.get_odata_response(service_root)
            self.assertIsNotNone(service_doc)

            # 2. Find a table to work with (preferably Students if available)
            table_name = None
            if "value" in service_doc and service_doc["value"]:
                # Look for a Students table or similar
                for entity in service_doc["value"]:
                    if "name" in entity:
                        if "student" in entity["name"].lower():
                            table_name = entity["name"]
                            break

                # If no students table found, use the first available table
                if not table_name and service_doc["value"]:
                    table_name = service_doc["value"][0]["name"]

            self.assertIsNotNone(table_name, "Could not find any tables in the database")
            print(f"Using table: {table_name}")

            # 3. Get records from the table with count option
            print(f"\nTesting get_records with table: {table_name}")
            records = self.hook.get_records(table=table_name, top=5, count=True)  # Limit to 5 records  # Include count

            self.assertIsNotNone(records)
            self.assertIn("value", records, "Response should contain 'value' property")

            total_count = records.get("@odata.count", "N/A")
            record_count = len(records.get("value", []))
            print(f"Retrieved {record_count} records out of total: {total_count}")

            # Mask the data for privacy reasons but show structure
            if record_count > 0:
                # Get the first record
                first_record = records["value"][0]

                # Create a masked version of the record for display
                masked_record = {}
                for key, value in first_record.items():
                    if isinstance(value, str) and len(value) > 4:
                        # Mask most of the string value
                        masked_record[key] = value[:2] + "*" * (len(value) - 4) + value[-2:]
                    else:
                        masked_record[key] = value

                print(f"Sample record structure (masked): {json.dumps(masked_record, indent=2)}")

                # 4. Test get_record_by_id
                if "@odata.id" in first_record or "id" in first_record:
                    # Extract record ID
                    record_id = None
                    if "@odata.id" in first_record:
                        # Extract ID from OData URL (format: URL/EntityName(ID))
                        odata_id = first_record["@odata.id"]
                        if "(" in odata_id and ")" in odata_id:
                            record_id = odata_id.split("(")[1].split(")")[0]
                    elif "id" in first_record:
                        record_id = first_record["id"]

                    if record_id:
                        print(f"\nTesting get_record_by_id with record ID: {record_id}")
                        single_record = self.hook.get_record_by_id(table=table_name, record_id=record_id)

                        self.assertIsNotNone(single_record, "Failed to retrieve record by ID")
                        print(f"Successfully retrieved record by ID (keys): {list(single_record.keys())}")

                        # 5. Test get_field_value
                        if single_record:
                            # Get first field name that appears to be a text field
                            potential_fields = []
                            for key, value in single_record.items():
                                if isinstance(value, str) and not key.startswith("@"):
                                    potential_fields.append(key)

                            if potential_fields:
                                field_name = potential_fields[0]
                                print(f"\nTesting get_field_value with field: {field_name}")

                                field_value = self.hook.get_field_value(
                                    table=table_name, record_id=record_id, field_name=field_name
                                )

                                self.assertIsNotNone(field_value, "Failed to retrieve field value")

                                # Mask the field value for privacy
                                if isinstance(field_value, str) and len(field_value) > 4:
                                    masked_value = field_value[:2] + "*" * (len(field_value) - 4) + field_value[-2:]
                                    print(f"Successfully retrieved field value (masked): {masked_value}")
                                else:
                                    print(f"Successfully retrieved field value (type): {type(field_value)}")

                                # 6. Test get_binary_field_value (if applicable)
                                # We'll check for fields that might contain binary data
                                binary_field_candidates = []
                                for key, value in single_record.items():
                                    if any(
                                        binary_term in key.lower()
                                        for binary_term in ["photo", "image", "file", "attachment", "binary", "blob"]
                                    ):
                                        binary_field_candidates.append(key)

                                if binary_field_candidates:
                                    binary_field = binary_field_candidates[0]
                                    print(f"\nTesting get_binary_field_value with field: {binary_field}")

                                    try:
                                        binary_data = self.hook.get_binary_field_value(
                                            table=table_name, record_id=record_id, field_name=binary_field
                                        )

                                        if binary_data:
                                            print(f"Successfully retrieved binary data, size: {len(binary_data)} bytes")
                                        else:
                                            print("Binary field returned no data")
                                    except Exception as e:
                                        print(f"Binary field retrieval failed: {str(e)}")
                                else:
                                    print("No potential binary fields found to test get_binary_field_value")
                            else:
                                print("No suitable text fields found to test get_field_value")
                    else:
                        print("Could not determine record ID to test get_record_by_id")
                else:
                    print("Record does not have a standard ID field to test get_record_by_id")
            else:
                print("No records retrieved to test get_record_by_id and get_field_value")

            # 7. Test get_cross_join if there are at least two tables
            if "value" in service_doc and len(service_doc["value"]) >= 2:
                table1 = service_doc["value"][0]["name"]
                table2 = service_doc["value"][1]["name"]

                print(f"\nTesting get_cross_join with tables: {table1} and {table2}")
                try:
                    cross_join_results = self.hook.get_cross_join(tables=[table1, table2], top=3)  # Limit to 3 results

                    self.assertIsNotNone(cross_join_results)

                    join_count = len(cross_join_results.get("value", []))
                    print(f"Cross join returned {join_count} results")

                    if join_count > 0:
                        # Show structure without exposing data
                        print(f"Cross join result keys: {list(cross_join_results['value'][0].keys())}")
                except Exception as e:
                    print(f"Cross join test failed: {str(e)}")
            else:
                print("Not enough tables available to test get_cross_join")

        except Exception as e:
            self.fail(f"Request data methods test failed with error: {str(e)}")


if __name__ == "__main__":
    unittest.main()
