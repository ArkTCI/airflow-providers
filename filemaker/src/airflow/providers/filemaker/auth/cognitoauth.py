"""
AuthCloudAuth module for FileMaker Cloud authentication.
"""

import re
import requests
from typing import Any, Dict, Optional

import boto3
from botocore.config import Config
from pycognito import Cognito

from airflow.utils.log.logging_mixin import LoggingMixin


class FileMakerCloudAuth(LoggingMixin):
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

        # Logger is automatically provided by LoggingMixin
        
        # Initialize token cache
        self._token = None
        
        # Initialize boto3 client for direct API access
        self._init_cognito_client()
        
        # Keep the pycognito Cognito instance for backwards compatibility
        boto3_config = Config(region_name=self.region, retries={"max_attempts": 3, "mode": "standard"})
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
        self._cognito_client = self.cognito

    def _init_cognito_client(self) -> None:
        """
        Initialize the boto3 Cognito client.
        """
        self.cognito_idp_client = boto3.client("cognito-idp", region_name=self.region)
        self.log.debug("Initialized boto3 Cognito client for region %s", self.region)

    def _create_cognito_client(self) -> None:
        """
        Create a Cognito client using pycognito.
        This method is kept for backward compatibility.
        """
        self._cognito_client = self.cognito
        self.log.debug("Created pycognito Cognito client for backward compatibility")

    def get_token(self) -> str:
        """
        Get a token from Cognito using direct API approach as recommended by Claris.

        Returns:
            str: The token.
        """
        # Return cached token if available
        if self._token:
            self.log.debug("Using cached authentication token")
            return self._token

        self.log.info("Authenticating user %s with FileMaker Cloud", self.username)

        try:
            # Use the direct API approach (similar to JS SDK method in FileMakerHook)
            auth_result = self._authenticate_direct_api()
            
            # Get the ID token
            token = auth_result.get("IdToken", "")
            if not token:
                self.log.error("Authentication succeeded but no token was returned")
                return ""

            # Mask the token length in logs for security
            self.log.debug("Received authentication token successfully")

            # Cache the token
            self._token = token

            return token
        except Exception as e:
            self.log.error("Authentication failed: %s", str(e), exc_info=True)
            # Return empty string instead of None or raising an exception
            return ""
            
    def _authenticate_direct_api(self) -> Dict[str, Any]:
        """
        Authenticate using direct API calls to Cognito, as recommended by Claris.

        This approach uses direct HTTP requests to the Cognito service.

        Returns:
            Dict[str, Any]: Authentication result
        """
        auth_url = f"https://cognito-idp.{self.region}.amazonaws.com/"

        headers = {
            "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
            "Content-Type": "application/x-amz-json-1.1",
        }

        payload = {
            "AuthFlow": "USER_PASSWORD_AUTH",
            "ClientId": self.client_id,
            "AuthParameters": {
                "USERNAME": self.username,
                "PASSWORD": self.password,
                "DEVICE_KEY": None,
            },
            "ClientMetadata": {},
        }

        self.log.info("Sending auth request to Cognito endpoint: %s", auth_url)
        
        # Make the request
        response = requests.post(auth_url, headers=headers, json=payload)

        if response.status_code != 200:
            error_msg = f"Authentication failed with status {response.status_code}: {response.text}"
            self.log.error("ERROR: %s", error_msg)
            raise Exception(error_msg)
            
        self.log.info("Authentication request successful with status code: %s", response.status_code)

        response_json = response.json()
        
        # Return the authentication result
        return response_json.get("AuthenticationResult", {})
