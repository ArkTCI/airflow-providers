"""
AuthCloudAuth module for FileMaker Cloud authentication.
"""

import logging
import re
from typing import Optional

from botocore.config import Config
from pycognito import Cognito


class FileMakerCloudAuth:
    """
    Authentication handler for FileMaker Cloud using AWS Cognito.

    This class handles authentication with AWS Cognito for FileMaker Cloud.
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
        """
        Initialize the FileMakerCloudAuth.

        Args:
            username: FileMaker Cloud username
            password: FileMaker Cloud password
            host: FileMaker Cloud host
            region: AWS region (optional)
            user_pool_id: Cognito user pool ID (optional)
            client_id: Cognito client ID (optional)
        """
        self.username = username
        self.password = password
        self.host = host

        # Get region from host if not provided
        if not region and host:
            # Extract region from host (e.g., fm-us-west-2.claris.com -> us-west-2)
            match = re.search(r"fm-([\w-]+)\.", host)
            self.region = match.group(1) if match else "us-west-2"
        else:
            self.region = region or "us-west-2"

        # Use provided pool and client IDs or get defaults
        self.user_pool_id = user_pool_id or f"{self.region}_NqkuZcXQY"
        self.client_id = client_id or "4l9rvl4mv5es1eep1qe97cautn"

        # Initialize Cognito client
        boto3_config = Config(region_name=self.region, retries={"max_attempts": 3, "mode": "standard"})

        # Initialize with boto3_client_kwargs to match test expectations
        boto3_client_kwargs = {
            "config": boto3_config,
            # Provide empty credentials to prevent boto3 from looking in ~/.aws/credentials
            "aws_access_key_id": "",
            "aws_secret_access_key": "",
        }

        self.cognito = Cognito(
            user_pool_id=self.user_pool_id,
            client_id=self.client_id,
            username=self.username,
            user_pool_region=self.region,
            boto3_client_kwargs=boto3_client_kwargs,
        )

        # Add the missing attributes
        self._token = None
        self._cognito_client = None

        # Configure boto3 client
        self.log = logging.getLogger(__name__)

    def _create_cognito_client(self) -> None:
        """
        Create a Cognito client.
        """
        self._cognito_client = self.cognito

    def get_token(self) -> str:
        """
        Get a token from Cognito.

        Returns:
            str: The token.
        """
        # Return cached token if available
        if self._token:
            self.log.debug("Using cached authentication token")
            return self._token

        self.log.info(f"Authenticating user {self.username} with FileMaker Cloud")

        try:
            # Authenticate using SRP (Secure Remote Password) protocol
            self.log.info("Initiating SRP authentication with Cognito")
            self.log.debug(f"Region: {self.region}, User Pool ID: {self.user_pool_id}, Client ID: {self.client_id}")

            # Create Cognito client if not already created
            if not self._cognito_client:
                self._create_cognito_client()
                self.log.debug("Created Cognito client")

            # Authenticate with Cognito - need to pass the password
            self.log.debug(f"Attempting to authenticate user: {self.username}")
            if not self.password:
                self.log.error("Password is empty or None")
                return ""

            self._cognito_client.authenticate(password=self.password)
            self.log.debug("Authentication successful")

            # Get the ID token
            token = self._cognito_client.id_token
            if not token:
                self.log.error("Authentication succeeded but no token was returned")
                return ""

            self.log.debug(f"Received token of length: {len(token)}")

            # Cache the token
            self._token = token

            return token
        except Exception as e:
            self.log.error(f"Authentication failed: {str(e)}")
            self.log.exception("Detailed exception information:")
            # Return empty string instead of None or raising an exception
            return ""
