"""
Authentication module for FileMaker Cloud.

This module handles authentication against the FileMaker Cloud Cognito service.
"""

import logging
from typing import Optional

import boto3
import requests


class FileMakerCloudAuth:
    """
    Handles authentication for FileMaker Cloud using AWS Cognito.

    :param username: The FileMaker Cloud username
    :type username: str
    :param password: The FileMaker Cloud password
    :type password: str
    :param host: The FileMaker Cloud host URL
    :type host: str
    :param region: AWS region for Cognito service, default is None (auto-detect)
    :type region: Optional[str]
    """

    def __init__(
        self, username: str, password: str, host: str, region: Optional[str] = None
    ) -> None:
        self.username = username
        self.password = password
        self.host = host
        self.region = region
        self._token = None
        self.client = None
        self.user_pool_id = None
        self.client_id = None
        self.log = logging.getLogger(__name__)

    def _get_pool_info(self) -> tuple:
        """
        Get the Cognito user pool information from the FileMaker Cloud host.

        :return: A tuple containing the user pool ID and client ID
        :rtype: tuple
        """
        self.log.info(f"Fetching Cognito user pool information from {self.host}")

        try:
            response = requests.get(f"{self.host}/fmi/odata/login/info")
            response.raise_for_status()

            data = response.json()

            self.user_pool_id = data["CognitoUserPool"]["UserPoolId"]
            self.client_id = data["CognitoUserPool"]["ClientId"]

            # If region was not provided, extract it from the user_pool_id
            if not self.region and "_" in self.user_pool_id:
                self.region = self.user_pool_id.split("_")[0]

            self.log.info(
                f"Retrieved pool info - Region: {self.region}, "
                f"UserPoolId: {self.user_pool_id}, ClientId: {self.client_id[:5]}..."
            )

            return (self.user_pool_id, self.client_id)

        except Exception as e:
            self.log.error(f"Error fetching pool info: {str(e)}")
            raise

    def _init_client(self) -> None:
        """
        Initialize the boto3 Cognito IDP client.
        This is separated to make testing easier.
        """
        if not self.client:
            if self.region:
                self.log.info(
                    f"Initializing boto3 Cognito client in region {self.region}"
                )
                self.client = boto3.client("cognito-idp", region_name=self.region)
            else:
                self.log.info("Initializing boto3 Cognito client with default region")
                self.client = boto3.client("cognito-idp")

    def get_token(self) -> str:
        """
        Get an authentication token for FileMaker Cloud.

        :return: The ID token to use for authentication
        :rtype: str
        """
        # Return cached token if available
        if self._token:
            self.log.debug("Using cached authentication token")
            return self._token

        self.log.info(f"Authenticating user {self.username} with FileMaker Cloud")

        # Get pool info if not already available
        if not self.user_pool_id or not self.client_id:
            self._get_pool_info()

        # Initialize boto3 client if not already done
        self._init_client()

        try:
            self.log.info("Initiating authentication with Cognito")
            response = self.client.initiate_auth(
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={"USERNAME": self.username, "PASSWORD": self.password},
                ClientId=self.client_id,
            )

            self._token = response["AuthenticationResult"]["IdToken"]
            self.log.info("Successfully obtained authentication token")
            return self._token

        except Exception as e:
            self.log.error(f"Authentication failed: {str(e)}")
            raise
