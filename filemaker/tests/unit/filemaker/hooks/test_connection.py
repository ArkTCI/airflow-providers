"""
Unit tests for the FileMaker connection testing functionality.
"""

import unittest
from unittest.mock import MagicMock, patch

from airflow.models.connection import Connection

from airflow.providers.filemaker.hooks.filemaker import FileMakerHook


class TestFileMakerHookConnectionTesting(unittest.TestCase):
    """Test class for FileMakerHook connection testing."""

    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_token")
    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_odata_response")
    def test_test_connection_success(self, mock_get_odata_response, mock_get_token):
        """Test test_connection method when connection is successful."""
        # Setup
        mock_get_token.return_value = "test-token"
        mock_get_odata_response.return_value = {"value": []}  # Mock API response

        mock_conn = MagicMock(spec=Connection)
        mock_conn.host = "test-host"
        mock_conn.schema = "test-db"
        mock_conn.login = "test-user"
        mock_conn.password = "test-password"

        # Execute
        result, message = FileMakerHook.test_connection(mock_conn)

        # Assert
        self.assertTrue(result)
        self.assertEqual(message, "Connection successful.")
        mock_get_token.assert_called_once()
        # Also verify the get_odata_response was called
        mock_get_odata_response.assert_called_once()

    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_token")
    def test_test_connection_failure_no_token(self, mock_get_token):
        """Test test_connection method when no token is returned."""
        # Setup
        mock_get_token.return_value = ""  # Empty token
        mock_conn = MagicMock(spec=Connection)
        mock_conn.host = "test-host"
        mock_conn.schema = "test-db"
        mock_conn.login = "test-user"
        mock_conn.password = "test-password"

        # Execute
        result, message = FileMakerHook.test_connection(mock_conn)

        # Assert
        self.assertFalse(result)
        self.assertEqual(message, "Failed to retrieve authentication token. Please verify your credentials.")
        mock_get_token.assert_called_once()

    @patch("airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_token")
    def test_test_connection_exception(self, mock_get_token):
        """Test test_connection method when an exception occurs."""
        # Setup
        mock_get_token.side_effect = Exception("Authentication failed")
        mock_conn = MagicMock(spec=Connection)
        mock_conn.host = "test-host"
        mock_conn.schema = "test-db"
        mock_conn.login = "test-user"
        mock_conn.password = "test-password"

        # Execute
        result, message = FileMakerHook.test_connection(mock_conn)

        # Assert
        self.assertFalse(result)
        self.assertEqual(message, "Connection failed (Exception): Authentication failed")
        mock_get_token.assert_called_once()

    def test_test_connection_missing_host(self):
        """Test test_connection method when host is missing."""
        # Setup
        mock_conn = MagicMock(spec=Connection)
        mock_conn.host = ""  # Empty host
        mock_conn.schema = "test-db"
        mock_conn.login = "test-user"
        mock_conn.password = "test-password"

        # Execute
        result, message = FileMakerHook.test_connection(mock_conn)

        # Assert
        self.assertFalse(result)
        self.assertEqual(message, "Missing FileMaker host in connection configuration")

    def test_test_connection_missing_database(self):
        """Test test_connection method when database is missing."""
        # Setup
        mock_conn = MagicMock(spec=Connection)
        mock_conn.host = "test-host"
        mock_conn.schema = ""  # Empty schema/database
        mock_conn.login = "test-user"
        mock_conn.password = "test-password"

        # Execute
        result, message = FileMakerHook.test_connection(mock_conn)

        # Assert
        self.assertFalse(result)
        self.assertEqual(message, "Missing FileMaker database in connection configuration")


if __name__ == "__main__":
    unittest.main()
