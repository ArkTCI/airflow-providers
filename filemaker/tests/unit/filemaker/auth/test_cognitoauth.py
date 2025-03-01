"""
Unit tests for the FileMaker Cloud authentication module.
"""
import unittest
from unittest.mock import patch, MagicMock

# Try the installed package path first, fall back to direct path for development
try:
    from airflow.providers.filemaker.auth.cognitoauth import FileMakerCloudAuth
except ImportError:
    from airflow.providers.filemaker.auth.cognitoauth import FileMakerCloudAuth


class TestFileMakerCloudAuth(unittest.TestCase):
    """Test class for FileMakerCloudAuth."""

    def test_init(self):
        """Test initialization with fixed credentials."""
        auth = FileMakerCloudAuth(username="test_user", password="test_pass", host="test-host")
        
        # Check that the fixed credentials are set
        self.assertEqual(auth.user_pool_id, "us-west-2_NqkuZcXQY")
        self.assertEqual(auth.client_id, "4l9rvl4mv5es1eep1qe97cautn")
        self.assertEqual(auth.region, "us-west-2")

    @patch('airflow.providers.filemaker.auth.cognitoauth.Cognito')
    def test_get_token(self, mock_cognito_class):
        """Test get_token method using pycognito."""
        # Setup mocks
        mock_cognito_instance = MagicMock()
        mock_cognito_class.return_value = mock_cognito_instance
        
        # Set the id_token attribute
        mock_cognito_instance.id_token = "test-id-token"

        # Execute method
        auth = FileMakerCloudAuth(username="test_user", password="test_pass", host="test-host")
        token = auth.get_token()

        # Assertions
        self.assertEqual(token, "test-id-token")
        
        # Verify Cognito was initialized correctly
        # Use ANY for the config object since it's not easily comparable
        from unittest.mock import ANY
        mock_cognito_class.assert_called_once_with(
            user_pool_id="us-west-2_NqkuZcXQY",
            client_id="4l9rvl4mv5es1eep1qe97cautn",
            username="test_user",
            user_pool_region="us-west-2",
            boto3_client_kwargs={"config": ANY}
        )
        
        # Verify authenticate was called with the password
        mock_cognito_instance.authenticate.assert_called_once_with(password="test_pass")


if __name__ == '__main__':
    unittest.main() 