"""
Unit tests for the FileMaker auth.
"""

import unittest
from unittest.mock import MagicMock, patch, ANY

import boto3
from moto import mock_aws

from airflow.providers.filemaker.auth.cognitoauth import FileMakerCloudAuth

# Try the installed package path first, fall back to direct path for development


class TestFileMakerCloudAuth(unittest.TestCase):
    """Test class for FileMakerCloudAuth."""

    @mock_aws
    def test_init(self):
        """Test initialization with fixed credentials."""
        # Create a mock user pool and client using moto
        cognito_client = boto3.client('cognito-idp', region_name='us-west-2')
        
        # Create a user pool
        user_pool = cognito_client.create_user_pool(
            PoolName='test-pool',
            UsernameAttributes=['email'],
        )
        
        # Create a client
        client = cognito_client.create_user_pool_client(
            UserPoolId=user_pool['UserPool']['Id'],
            ClientName='test-client',
            GenerateSecret=False,
        )
        
        # Now test our class with the mocked AWS environment
        auth = FileMakerCloudAuth(
            username="test_user", 
            password="test_pass", 
            host="test-host",
            user_pool_id=user_pool['UserPool']['Id'],
            client_id=client['UserPoolClient']['ClientId']
        )

        # Check that the credentials are set
        self.assertEqual(auth.user_pool_id, user_pool['UserPool']['Id'])
        self.assertEqual(auth.client_id, client['UserPoolClient']['ClientId'])
        self.assertEqual(auth.region, "us-west-2")

    @patch("airflow.providers.filemaker.auth.cognitoauth.Cognito")
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
        mock_cognito_class.assert_called_once_with(
            user_pool_id="us-west-2_NqkuZcXQY",
            client_id="4l9rvl4mv5es1eep1qe97cautn",
            username="test_user",
            user_pool_region="us-west-2",
            boto3_client_kwargs={"config": ANY}
        )

        # Verify authenticate_user was called
        mock_cognito_instance.authenticate_user.assert_called_once()


if __name__ == "__main__":
    unittest.main()
