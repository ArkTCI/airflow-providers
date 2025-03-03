"""
AuthCloudAuth module for FileMaker Cloud authentication.
"""

import logging
from typing import Optional

import botocore
from botocore.config import Config
from pycognito import Cognito


class FileMakerCloudAuth:
    """
    FileMakerCloudAuth is a class for authenticating with FileMaker Cloud.

    This class handles authentication with FileMaker Cloud's OData API using AWS Cognito.
    It can either use provided Cognito details or discover them from the FileMaker Cloud endpoint.

    :param username: FileMaker Cloud username (Claris ID)
    :type username: str
    :param password: FileMaker Cloud password
    :type password: str
    :param host: FileMaker Cloud host URL
    :type host: str
    :param region: AWS region for Cognito (optional, will be extracted from user_pool_id if not provided)
    :type region: str
    :param user_pool_id: Cognito user pool ID (optional, will be discovered from host if not provided)
    :type user_pool_id: str
    :param client_id: Cognito client ID (optional, will be discovered from host if not provided)
    :type client_id: str
    """

    def __init__(
        self,
        username: str,
        password: str,
        host: str,
        region: Optional[str] = None,
        user_pool_id: Optional[str] = None,
        client_id: Optional[str] = None,
    ) -> None:
        self.username = username
        self.password = password
        self.host = host
        self.region = region
        self._token = None
        self.client = None

        # Use fixed Cognito pool credentials or provided ones
        self.user_pool_id = user_pool_id or "us-west-2_NqkuZcXQY"
        self.client_id = client_id or "4l9rvl4mv5es1eep1qe97cautn"

        # Set region from user_pool_id if not provided
        if not self.region and "_" in self.user_pool_id:
            self.region = self.user_pool_id.split("_")[0]

        self.log = logging.getLogger(__name__)

        # Initialize the Cognito client using pycognito
        # Configure boto3 client with unsigned requests to avoid looking for AWS credentials
        boto_config = Config(signature_version=botocore.UNSIGNED, retries={"max_attempts": 3})

        self.cognito = Cognito(
            user_pool_id=self.user_pool_id,
            client_id=self.client_id,
            username=self.username,
            user_pool_region=self.region,
            boto3_client_kwargs={"config": boto_config},
        )

    def get_token(self) -> str:
        """
        Get a token from Cognito.
        
        Returns:
            str: The token.
        """
        try:
            # Return cached token if available
            if self._token:
                self.log.debug("Using cached authentication token")
                return self._token

            self.log.info(f"Authenticating user {self.username} with FileMaker Cloud")

            # Authenticate using SRP (Secure Remote Password) protocol
            self.log.info("Initiating SRP authentication with Cognito")

            # pycognito handles all the SRP calculations internally
            self.cognito.authenticate(password=self.password)

            # Get the ID token
            self._token = self.cognito.id_token

            self.log.info("Successfully obtained authentication token")
            return self._token

        except Exception as e:
            self.log.error(f"Error getting token: {e}")
            return ""  # Return empty string instead of None
