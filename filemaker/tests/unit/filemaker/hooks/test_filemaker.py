"""
Unit tests for the FileMaker hook.
"""
import unittest
from unittest.mock import patch, MagicMock

# Try the installed package path first, fall back to direct path for development
try:
    from airflow.providers.filemaker.hooks.filemaker import FileMakerHook
except ImportError:
    from airflow.providers.filemaker.hooks.filemaker import FileMakerHook


class TestFileMakerHook(unittest.TestCase):
    """Test class for FileMakerHook."""

    @patch('airflow.providers.filemaker.hooks.filemaker.requests')
    def test_get_base_url(self, mock_requests):
        """Test get_base_url method."""
        hook = FileMakerHook(host="test-host", database="test-db")
        url = hook.get_base_url()
        self.assertEqual(url, "https://test-host/fmi/odata/v4/test-db")

    @patch('airflow.providers.filemaker.hooks.filemaker.requests')
    def test_get_base_url_with_protocol(self, mock_requests):
        """Test get_base_url method with protocol in host."""
        hook = FileMakerHook(host="https://test-host", database="test-db")
        url = hook.get_base_url()
        self.assertEqual(url, "https://test-host/fmi/odata/v4/test-db")

    @patch('airflow.providers.filemaker.hooks.filemaker.FileMakerHook.get_token')
    @patch('airflow.providers.filemaker.hooks.filemaker.requests.get')
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
            params=None
        )


if __name__ == '__main__':
    unittest.main() 