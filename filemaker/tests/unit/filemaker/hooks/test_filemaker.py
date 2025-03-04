"""
Unit tests for the FileMaker hook.
"""

import sys
import unittest
import warnings
from unittest.mock import MagicMock, patch

from airflow.providers.filemaker.hooks.filemaker import FileMakerHook


class TestFileMakerHook(unittest.TestCase):
    """Test class for FileMakerHook."""

    @patch("airflow.providers.filemaker.hooks.filemaker.requests")
    def test_get_base_url(self, mock_requests):
        """Test get_base_url method."""
        hook = FileMakerHook(host="test-host", database="test-db")
        url = hook.get_base_url()
        self.assertEqual(url, "https://test-host/fmi/odata/v4/test-db")

    @patch("airflow.providers.filemaker.hooks.filemaker.requests")
    def test_get_base_url_with_protocol(self, mock_requests):
        """Test get_base_url method with protocol in host."""
        hook = FileMakerHook(host="https://test-host", database="test-db")
        url = hook.get_base_url()
        self.assertEqual(url, "https://test-host/fmi/odata/v4/test-db")

    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_token")
    @patch("airflow.providers.filemaker.hooks.filemaker.requests.get")
    def test_get_odata_response(self, mock_get, mock_get_token):
        """Test get_odata_response method."""
        mock_get_token.return_value = "test-token"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"value": [{"id": 1}]}
        mock_get.return_value = mock_response

        hook = FileMakerHook(host="test-host", database="test-db")
        result = hook.get_odata_response("https://test-endpoint")

        self.assertEqual(result, {"value": [{"id": 1}]})
        mock_get.assert_called_once_with(
            "https://test-endpoint",
            headers={"Authorization": "FMID test-token", "Accept": "application/json"},
            params=None,
        )

    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_odata_response")
    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_base_url")
    def test_get_records_with_query_options(self, mock_get_base_url, mock_get_odata_response):
        """Test get_records method with all query options."""
        mock_get_base_url.return_value = "https://test-host/fmi/odata/v4/test-db"
        mock_get_odata_response.return_value = {"value": [{"id": 1}]}

        hook = FileMakerHook(host="test-host", database="test-db")

        # Test with all query options
        result = hook.get_records(
            table="MyTable",
            select="id,name",
            filter_query="name eq 'Test'",
            top=10,
            skip=5,
            orderby="name asc",
            expand="RelatedTable",
            count=True,
            apply="groupby((Category),aggregate(Amount with sum as TotalAmount))",
        )

        self.assertEqual(result, {"value": [{"id": 1}]})
        mock_get_odata_response.assert_called_once_with(
            endpoint="https://test-host/fmi/odata/v4/test-db/MyTable",
            params={
                "$select": "id,name",
                "$filter": "name eq 'Test'",
                "$top": 10,
                "$skip": 5,
                "$orderby": "name asc",
                "$expand": "RelatedTable",
                "$count": "true",
                "$apply": "groupby((Category),aggregate(Amount with sum as TotalAmount))",
            },
        )

    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_odata_response")
    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_base_url")
    def test_get_record_by_id(self, mock_get_base_url, mock_get_odata_response):
        """Test get_record_by_id method."""
        mock_get_base_url.return_value = "https://test-host/fmi/odata/v4/test-db"
        mock_get_odata_response.return_value = {"id": "123", "name": "Test Record"}

        hook = FileMakerHook(host="test-host", database="test-db")

        # Test with basic parameters
        result = hook.get_record_by_id(table="MyTable", record_id="123")

        self.assertEqual(result, {"id": "123", "name": "Test Record"})
        mock_get_odata_response.assert_called_once_with(
            endpoint="https://test-host/fmi/odata/v4/test-db/MyTable(123)", params={}
        )

        # Reset mocks
        mock_get_odata_response.reset_mock()

        # Test with select and expand
        result = hook.get_record_by_id(table="MyTable", record_id="123", select="id,name", expand="RelatedTable")

        self.assertEqual(result, {"id": "123", "name": "Test Record"})
        mock_get_odata_response.assert_called_once_with(
            endpoint="https://test-host/fmi/odata/v4/test-db/MyTable(123)",
            params={"$select": "id,name", "$expand": "RelatedTable"},
        )

    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_odata_response")
    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_base_url")
    def test_get_field_value(self, mock_get_base_url, mock_get_odata_response):
        """Test get_field_value method."""
        mock_get_base_url.return_value = "https://test-host/fmi/odata/v4/test-db"
        mock_get_odata_response.return_value = {"value": "Test Value"}

        hook = FileMakerHook(host="test-host", database="test-db")

        result = hook.get_field_value(table="MyTable", record_id="123", field_name="name")

        self.assertEqual(result, "Test Value")
        mock_get_odata_response.assert_called_once_with(
            endpoint="https://test-host/fmi/odata/v4/test-db/MyTable(123)/name"
        )

    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_binary_field")
    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_base_url")
    def test_get_binary_field_value(self, mock_get_base_url, mock_get_binary_field):
        """Test get_binary_field_value method."""
        mock_get_base_url.return_value = "https://test-host/fmi/odata/v4/test-db"
        mock_get_binary_field.return_value = b"binary data"

        hook = FileMakerHook(host="test-host", database="test-db")

        # Test with default accept format
        result = hook.get_binary_field_value(table="MyTable", record_id="123", field_name="attachment")

        self.assertEqual(result, b"binary data")
        mock_get_binary_field.assert_called_once_with(
            "https://test-host/fmi/odata/v4/test-db/MyTable(123)/attachment/$value", None
        )

        # Reset mocks
        mock_get_binary_field.reset_mock()

        # Test with custom accept format
        result = hook.get_binary_field_value(
            table="MyTable", record_id="123", field_name="image", accept_format="image/jpeg"
        )

        self.assertEqual(result, b"binary data")
        mock_get_binary_field.assert_called_once_with(
            "https://test-host/fmi/odata/v4/test-db/MyTable(123)/image/$value", "image/jpeg"
        )

    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_odata_response")
    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_base_url")
    def test_get_cross_join(self, mock_get_base_url, mock_get_odata_response):
        """Test get_cross_join method."""
        mock_get_base_url.return_value = "https://test-host/fmi/odata/v4/test-db"
        mock_get_odata_response.return_value = {"value": [{"Table1_id": 1, "Table2_name": "Test"}]}

        hook = FileMakerHook(host="test-host", database="test-db")

        # Test with basic parameters
        result = hook.get_cross_join(tables=["Table1", "Table2"])

        self.assertEqual(result, {"value": [{"Table1_id": 1, "Table2_name": "Test"}]})
        mock_get_odata_response.assert_called_once_with(
            endpoint="https://test-host/fmi/odata/v4/test-db/$crossjoin(Table1,Table2)", params={}
        )

        # Reset mocks
        mock_get_odata_response.reset_mock()

        # Test with query options
        result = hook.get_cross_join(
            tables=["Table1", "Table2"],
            select="Table1/id,Table2/name",
            filter_query="Table1/id eq 1",
            top=10,
            skip=5,
            orderby="Table1/id asc",
        )

        self.assertEqual(result, {"value": [{"Table1_id": 1, "Table2_name": "Test"}]})
        mock_get_odata_response.assert_called_once_with(
            endpoint="https://test-host/fmi/odata/v4/test-db/$crossjoin(Table1,Table2)",
            params={
                "$select": "Table1/id,Table2/name",
                "$filter": "Table1/id eq 1",
                "$top": 10,
                "$skip": 5,
                "$orderby": "Table1/id asc",
            },
        )

    def test_validate_url_length(self):
        """Test validate_url_length method with normal and long URLs."""
        hook = FileMakerHook(host="test-host", database="test-db")

        # Test with normal URL (positive case)
        normal_url = "https://test-host/fmi/odata/v4/test-db/Students"
        params = {"$select": "Name,Grade"}

        # This should not raise a warning
        with warnings.catch_warnings(record=True) as w:
            result = hook.validate_url_length(normal_url, params)
            sys.stderr.write(f"\nDEBUG - Normal URL Result: {result}\n")
            self.assertEqual(len(w), 0)  # No warnings should be raised
            self.assertTrue(result.startswith(normal_url))
            # Check URL parameter encoding - specific syntax of the encoded URL
            self.assertTrue("?%24select=Name%2CGrade" in result)

        # Test with very long URL that exceeds limit (negative case)
        long_url = "https://test-host/fmi/odata/v4/test-db/VeryLongTableName"
        # Generate a very long filter query
        long_filter = "Name eq '" + "x" * 2000 + "'"
        long_params = {"$filter": long_filter}

        # This should raise a warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")  # Ensure all warnings are shown
            result = hook.validate_url_length(long_url, long_params)
            sys.stderr.write(f"\nDEBUG - Long URL Result (truncated): {result[:100]}...\n")
            self.assertGreaterEqual(len(w), 1)  # At least one warning should be raised
            self.assertTrue(
                any("exceeds FileMaker's recommended 2000 character limit" in str(warning.message) for warning in w)
            )
            self.assertTrue(result.startswith(long_url))
            self.assertTrue("?%24filter=" in result)

    @patch("airflow.providers.filemaker.hooks.filemaker.requests.post")
    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_token")
    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.validate_url_length")
    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_base_url")
    def test_create_record_with_url_validation(
        self, mock_get_base_url, mock_validate_url_length, mock_get_token, mock_post
    ):
        """Test create_record method validates URL length."""
        # Setup mocks
        mock_get_base_url.return_value = "https://test-host/fmi/odata/v4/test-db"
        mock_get_token.return_value = "test-token"
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "123", "name": "Test Record"}
        mock_post.return_value = mock_response

        # Create hook and call method
        hook = FileMakerHook(host="test-host", database="test-db")
        result = hook.create_record(
            database="test-db", layout="Students", record_data={"name": "John Doe", "grade": "A"}
        )

        # Verify URL validation was called
        expected_endpoint = "https://test-host/fmi/odata/v4/test-db/Students"
        mock_validate_url_length.assert_called_once_with(expected_endpoint)

        # Verify the result
        self.assertEqual(result, {"id": "123", "name": "Test Record"})

    @patch("airflow.providers.filemaker.hooks.filemaker.requests.patch")
    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_token")
    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.validate_url_length")
    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_base_url")
    def test_update_record_with_url_validation(
        self, mock_get_base_url, mock_validate_url_length, mock_get_token, mock_patch
    ):
        """Test update_record method validates URL length."""
        # Setup mocks
        mock_get_base_url.return_value = "https://test-host/fmi/odata/v4/test-db"
        mock_get_token.return_value = "test-token"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123", "name": "Updated Record"}
        mock_patch.return_value = mock_response

        # Create hook and call method
        hook = FileMakerHook(host="test-host", database="test-db")
        result = hook.update_record(
            database="test-db", layout="Students", record_id="123", record_data={"name": "Updated Name", "grade": "A+"}
        )

        # Verify URL validation was called
        expected_endpoint = "https://test-host/fmi/odata/v4/test-db/Students(123)"
        mock_validate_url_length.assert_called_once_with(expected_endpoint)

        # Verify the result
        self.assertEqual(result, {"id": "123", "name": "Updated Record"})

    @patch("airflow.providers.filemaker.hooks.filemaker.requests.delete")
    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_token")
    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.validate_url_length")
    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_base_url")
    def test_delete_record_with_url_validation(
        self, mock_get_base_url, mock_validate_url_length, mock_get_token, mock_delete
    ):
        """Test delete_record method validates URL length."""
        # Setup mocks
        mock_get_base_url.return_value = "https://test-host/fmi/odata/v4/test-db"
        mock_get_token.return_value = "test-token"
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response

        # Create hook and call method
        hook = FileMakerHook(host="test-host", database="test-db")
        result = hook.delete_record(database="test-db", layout="Students", record_id="123")

        # Verify URL validation was called
        expected_endpoint = "https://test-host/fmi/odata/v4/test-db/Students(123)"
        mock_validate_url_length.assert_called_once_with(expected_endpoint)

        # Verify the result
        self.assertTrue(result)

    @patch("airflow.providers.filemaker.hooks.filemaker.requests.post")
    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_token")
    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.validate_url_length")
    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_base_url")
    def test_bulk_create_records_with_url_validation(
        self, mock_get_base_url, mock_validate_url_length, mock_get_token, mock_post
    ):
        """Test bulk_create_records method validates URL length."""
        # Setup mocks
        mock_get_base_url.return_value = "https://test-host/fmi/odata/v4/test-db"
        mock_get_token.return_value = "test-token"

        # Mock two successful responses for the two records
        mock_response1 = MagicMock()
        mock_response1.status_code = 201
        mock_response1.json.return_value = {"id": "123", "name": "Record 1"}

        mock_response2 = MagicMock()
        mock_response2.status_code = 201
        mock_response2.json.return_value = {"id": "124", "name": "Record 2"}

        mock_post.side_effect = [mock_response1, mock_response2]

        # Create hook and call method
        hook = FileMakerHook(host="test-host", database="test-db")
        result = hook.bulk_create_records(
            database="test-db",
            layout="Students",
            records_data=[{"name": "John Doe", "grade": "A"}, {"name": "Jane Smith", "grade": "B"}],
        )

        # Verify URL validation was called
        expected_endpoint = "https://test-host/fmi/odata/v4/test-db/Students"
        mock_validate_url_length.assert_called_once_with(expected_endpoint)

        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], {"id": "123", "name": "Record 1"})
        self.assertEqual(result[1], {"id": "124", "name": "Record 2"})

    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_odata_response")
    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.validate_url_length")
    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_base_url")
    def test_execute_function_with_url_validation(
        self, mock_get_base_url, mock_validate_url_length, mock_get_odata_response
    ):
        """Test execute_function method validates URL length."""
        # Setup mocks
        mock_get_base_url.return_value = "https://test-host/fmi/odata/v4/test-db"
        mock_get_odata_response.return_value = {"result": "success"}

        # Create hook and call method
        hook = FileMakerHook(host="test-host", database="test-db")
        result = hook.execute_function(
            database="test-db", layout="Students", script_name="UpdateGrades", script_params={"grade": "A+"}
        )

        # Verify URL validation was called with the right params
        expected_endpoint = "https://test-host/fmi/odata/v4/test-db/Students/script"
        expected_params = {"script": "UpdateGrades", "script-params": '{"grade": "A+"}'}
        mock_validate_url_length.assert_called_once_with(expected_endpoint, expected_params)

        # Verify get_odata_response was called properly
        mock_get_odata_response.assert_called_once_with(endpoint=expected_endpoint, params=expected_params)

        # Verify the result
        self.assertEqual(result, {"result": "success"})


if __name__ == "__main__":
    unittest.main()
