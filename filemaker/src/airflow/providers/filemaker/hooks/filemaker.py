"""
FileMaker Cloud OData Hook for interacting with FileMaker Cloud.
"""

import json
import logging
from typing import Any, Dict, Optional, Union

import boto3
import requests
from airflow.exceptions import AirflowException
from airflow.hooks.base import BaseHook

# Import the auth module
from airflow.providers.filemaker.auth.cognitoauth import FileMakerCloudAuth


class FileMakerHook(BaseHook):
    """
    Hook for FileMaker Cloud OData API.

    This hook handles authentication and API requests to FileMaker Cloud's OData API.

    :param host: FileMaker Cloud host URL
    :type host: str
    :param database: FileMaker database name
    :type database: str
    :param username: FileMaker Cloud username
    :type username: str
    :param password: FileMaker Cloud password
    :type password: str
    :param filemaker_conn_id: The connection ID to use from Airflow connections
    :type filemaker_conn_id: str
    """

    conn_name_attr = "filemaker_conn_id"
    default_conn_name = "filemaker_default"
    conn_type = "filemaker"
    hook_name = "FileMaker Cloud"

    # Define the form fields for the UI connection form
    @staticmethod
    def get_ui_field_behaviour():
        """
        Returns custom field behavior for the Airflow connection UI.
        """
        return {
            "hidden_fields": [],
            "relabeling": {
                "host": "FileMaker Host",
                "schema": "FileMaker Database",
                "login": "Username",
                "password": "Password",
            },
            "placeholders": {
                "host": "cloud.filemaker.com",
                "schema": "your-database",
                "login": "username",
                "password": "password",
            },
        }

    def __init__(
        self,
        host: Optional[str] = None,
        database: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        filemaker_conn_id: str = "filemaker_default",
    ) -> None:
        super().__init__()
        self.host = host
        self.database = database
        self.username = username
        self.password = password
        self.filemaker_conn_id = filemaker_conn_id
        self.auth = None
        self._cached_token = None
        self.cognito_idp_client = None
        self.user_pool_id = None
        self.client_id = None
        self.region = None

        # If connection ID is provided, get connection info
        if filemaker_conn_id:
            self._get_conn_info()

    def _get_conn_info(self) -> None:
        """
        Get connection info from Airflow connection.
        """
        try:
            conn = BaseHook.get_connection(self.filemaker_conn_id)
            self.host = self.host or conn.host
            self.database = self.database or conn.schema
            self.username = self.username or conn.login
            self.password = self.password or conn.password
        except Exception as e:
            # Log the error but don't fail - we might have params passed directly
            self.log.error(f"Error getting connection info: {str(e)}")

    def get_conn(self):
        """
        Get connection to FileMaker Cloud.

        :return: A connection object
        """
        if not self.auth:
            # Initialize the auth object
            self.auth = FileMakerCloudAuth(host=self.host, username=self.username, password=self.password)

        # Return a connection-like object that can be used by other methods
        return {"host": self.host, "database": self.database, "auth": self.auth, "base_url": self.get_base_url()}

    def get_base_url(self) -> str:
        """
        Get the base URL for the OData API.

        :return: The base URL
        :rtype: str
        """
        if not self.host or not self.database:
            raise ValueError("Host and database must be provided")

        # Check if host already has a protocol prefix
        host = self.host
        if host.startswith(("http://", "https://")):
            # Keep the host as is without adding https://
            base_url = f"{host}/fmi/odata/v4/{self.database}"
        else:
            # Add https:// if not present
            base_url = f"https://{host}/fmi/odata/v4/{self.database}"

        return base_url

    def get_token(self) -> str:
        """
        Get the authentication token.

        :return: The authentication token
        :rtype: str
        """
        if not self.auth:
            if not self.host or not self.username or not self.password:
                raise ValueError("Host, username, and password must be provided")

            self.auth = FileMakerCloudAuth(username=self.username, password=self.password, host=self.host)

        try:
            # Try to get the token from AWS Cognito
            return self.auth.get_token()
        except Exception as e:
            self.log.error(f"Error getting token: {str(e)}")
            raise AirflowException(f"Failed to get authentication token: {str(e)}")

    def get_odata_response(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        accept_format: str = "application/json",
    ) -> Union[Dict[str, Any], str]:
        """
        Execute an OData request and return the response.

        :param endpoint: The OData endpoint to call
        :type endpoint: str
        :param params: Query parameters to include
        :type params: Optional[Dict[str, Any]]
        :param accept_format: The Accept header format
        :type accept_format: str
        :return: The response data
        :rtype: Union[Dict[str, Any], str]
        """
        # Get token for authorization
        token = self.get_token()

        # Prepare headers
        headers = {"Authorization": f"FMID {token}", "Accept": accept_format}

        # Execute request
        response = requests.get(endpoint, headers=headers, params=params)

        # Check response
        if response.status_code >= 400:
            raise Exception(f"OData API error: {response.status_code} - {response.text}")

        # Return appropriate format based on accept header
        if accept_format == "application/json":
            return response.json()
        else:
            return response.text

    def get_records(
        self,
        table: str,
        select: Optional[str] = None,
        filter_query: Optional[str] = None,
        top: Optional[int] = None,
        skip: Optional[int] = None,
        orderby: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch records from a FileMaker table using OData query options.

        :param table: The table name
        :type table: str
        :param select: $select parameter - comma-separated list of fields
        :type select: Optional[str]
        :param filter_query: $filter parameter - filtering condition
        :type filter_query: Optional[str]
        :param top: $top parameter - maximum number of records to return
        :type top: Optional[int]
        :param skip: $skip parameter - number of records to skip
        :type skip: Optional[int]
        :param orderby: $orderby parameter - sorting field(s)
        :type orderby: Optional[str]
        :return: The query results
        :rtype: Dict[str, Any]
        """
        base_url = self.get_base_url()
        endpoint = f"{base_url}/{table}"

        # Build query parameters
        params = {}
        if select:
            params["$select"] = select
        if filter_query:
            params["$filter"] = filter_query
        if top:
            params["$top"] = top
        if skip:
            params["$skip"] = skip
        if orderby:
            params["$orderby"] = orderby

        # Execute request
        return self.get_odata_response(endpoint=endpoint, params=params)

    def get_pool_info(self) -> Dict[str, str]:
        """
        Return fixed Cognito pool information for FileMaker Cloud.

        Uses the same credentials as the JavaScript implementation.

        :return: Dict containing Region, UserPool_ID, Client_ID
        :rtype: Dict[str, str]
        """
        # Use fixed Cognito credentials specific to FileMaker Cloud
        pool_info = {
            "Region": "us-west-2",
            "UserPool_ID": "us-west-2_NqkuZcXQY",
            "Client_ID": "4l9rvl4mv5es1eep1qe97cautn",
        }

        self.log.info(
            f"Using fixed FileMaker Cloud Cognito credentials: Region={pool_info.get('Region')}, "
            f"UserPool_ID={pool_info.get('UserPool_ID')}, "
            f"Client_ID={pool_info.get('Client_ID')[:5]}..."
        )

        return pool_info

    def get_fmid_token(self, username: Optional[str] = None, password: Optional[str] = None) -> str:
        """
        Get FileMaker ID token - direct equivalent to getFMIDToken in JS

        This is the main method that should be used for authentication.
        It returns only the ID token needed for API authentication.

        :param username: FileMaker Cloud username (Claris ID), defaults to connection username
        :type username: Optional[str]
        :param password: FileMaker Cloud password, defaults to connection password
        :type password: Optional[str]
        :return: ID token for use with FileMaker APIs
        :rtype: str
        """
        if self._cached_token:
            return self._cached_token

        auth_result = self.authenticate_user(username or self.username, password or self.password)
        self._cached_token = auth_result.get("id_token")
        return self._cached_token

    def authenticate_user(self, username: str, password: str, mfa_code: Optional[str] = None) -> Dict[str, str]:
        """
        Authenticate user and retrieve all tokens

        This method returns all tokens (access token, ID token, and refresh token)
        in the same format as the JavaScript SDK example in the Claris documentation.

        :param username: FileMaker Cloud username (Claris ID)
        :type username: str
        :param password: FileMaker Cloud password
        :type password: str
        :param mfa_code: MFA verification code if required
        :type mfa_code: Optional[str]
        :return: Dict containing access_token, id_token, and refresh_token
        :rtype: Dict[str, str]
        """
        self.log.info(f"Authenticating user '{username}' with Cognito...")

        try:
            # Initialize Cognito client if not already done
            if not self.cognito_idp_client:
                pool_info = self.get_pool_info()
                self.user_pool_id = pool_info["UserPool_ID"]
                self.client_id = pool_info["Client_ID"]
                self.region = pool_info["Region"]
                self.cognito_idp_client = boto3.client("cognito-idp", region_name=self.region)

            # This implementation follows the official Claris documentation
            auth_result = self._authenticate_js_sdk_equivalent(username, password, mfa_code)

            # Parse the response similar to the JS SDK
            tokens = {
                "access_token": auth_result.get("AccessToken"),  # Equivalent to result.getAccessToken().getJwtToken()
                "id_token": auth_result.get("IdToken"),  # Equivalent to result.idToken.jwtToken
                "refresh_token": auth_result.get("RefreshToken"),  # Equivalent to result.refreshToken.token
            }

            self.log.info("Authentication successful. Retrieved access, ID, and refresh tokens.")
            return tokens

        except Exception as e:
            self.log.error(f"Authentication failed: {str(e)}")

            # Try fallback methods
            for method_name, method in [
                ("Direct API", self._authenticate_direct_api),
                ("USER_PASSWORD_AUTH", self._authenticate_user_password),
                ("ADMIN_USER_PASSWORD_AUTH", self._authenticate_admin),
            ]:
                try:
                    self.log.info(f"Trying fallback method: {method_name}")
                    result = method(username, password)
                    if isinstance(result, dict) and "IdToken" in result:
                        return {
                            "access_token": result.get("AccessToken"),
                            "id_token": result.get("IdToken"),
                            "refresh_token": result.get("RefreshToken"),
                        }
                    elif isinstance(result, str):
                        # If the method only returned the ID token
                        return {"id_token": result}
                except Exception as fallback_error:
                    self.log.error(f"{method_name} fallback failed: {str(fallback_error)}")
                    continue

            # All methods failed
            raise AirflowException(f"All authentication methods failed. Original error: {str(e)}")

    def refresh_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Use refresh token to get new access and ID tokens

        The refresh token is valid for 1 year according to Claris documentation.

        :param refresh_token: The refresh token from a previous authentication
        :type refresh_token: str
        :return: Dict containing new access_token and id_token
        :rtype: Dict[str, str]
        """
        self.log.info("Refreshing tokens using refresh token...")

        try:
            response = self.cognito_idp_client.initiate_auth(
                AuthFlow="REFRESH_TOKEN_AUTH",
                ClientId=self.client_id,
                AuthParameters={"REFRESH_TOKEN": refresh_token},
            )

            auth_result = response.get("AuthenticationResult", {})

            tokens = {
                "access_token": auth_result.get("AccessToken"),
                "id_token": auth_result.get("IdToken"),
                # Note: A new refresh token is not provided during refresh
            }

            self.log.info("Successfully refreshed tokens.")
            return tokens

        except Exception as e:
            self.log.error(f"Token refresh failed: {str(e)}")
            raise AirflowException(f"Failed to refresh tokens: {str(e)}")

    def _authenticate_js_sdk_equivalent(
        self, username: str, password: str, mfa_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Authenticate using approach equivalent to JavaScript SDK's authenticateUser

        This mimics how the JS SDK's CognitoUser.authenticateUser works as shown
        in the official Claris documentation.

        :param username: FileMaker Cloud username
        :type username: str
        :param password: FileMaker Cloud password
        :type password: str
        :param mfa_code: MFA verification code if required
        :type mfa_code: Optional[str]
        :return: Authentication result including tokens
        :rtype: Dict[str, Any]
        """
        auth_url = f"https://cognito-idp.{self.region}.amazonaws.com/"

        # Create headers similar to the JS SDK
        headers = {
            "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
            "Content-Type": "application/x-amz-json-1.1",
        }

        # Create payload similar to how the JS SDK formats it
        payload = {
            "AuthFlow": "USER_PASSWORD_AUTH",
            "ClientId": self.client_id,
            "AuthParameters": {
                "USERNAME": username,
                "PASSWORD": password,
                "DEVICE_KEY": None,
            },
            "ClientMetadata": {},
        }

        self.log.info(f"Sending auth request to Cognito endpoint: {auth_url}")

        # Make the request
        response = requests.post(auth_url, headers=headers, json=payload)

        self.log.info(f"Response status code: {response.status_code}")

        if response.status_code != 200:
            error_msg = f"Authentication failed with status {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f": {error_data.get('__type', '')} - {error_data.get('message', response.text)}"
            except json.JSONDecodeError:
                error_msg += f": {response.text}"

            self.log.error(f"ERROR: {error_msg}")
            raise AirflowException(error_msg)

        # Parse response
        response_json = response.json()

        # Check for MFA challenge
        if "ChallengeName" in response_json:
            challenge_name = response_json["ChallengeName"]
            self.log.info(f"Authentication requires challenge: {challenge_name}")

            if challenge_name in ["SMS_MFA", "SOFTWARE_TOKEN_MFA"]:
                if not mfa_code:
                    raise AirflowException(f"MFA is required ({challenge_name}). Please provide an MFA code.")

                # Handle MFA challenge similar to JS SDK's sendMFACode
                return self._respond_to_auth_challenge(username, challenge_name, mfa_code, response_json)
            elif challenge_name == "NEW_PASSWORD_REQUIRED":
                raise AirflowException(
                    "Account requires password change. Please update password through the FileMaker Cloud portal."
                )
            else:
                raise AirflowException(f"Unsupported challenge type: {challenge_name}")

        # Return the authentication result
        auth_result = response_json.get("AuthenticationResult", {})

        if not auth_result.get("IdToken"):
            error_msg = "Authentication succeeded but no ID token was returned"
            self.log.error(f"ERROR: {error_msg}")
            raise AirflowException(error_msg)

        self.log.info(
            f"Successfully obtained tokens. ID token first 20 chars: {auth_result.get('IdToken', '')[:20]}..."
        )
        return auth_result

    def _respond_to_auth_challenge(
        self,
        username: str,
        challenge_name: str,
        mfa_code: str,
        challenge_response: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Respond to an authentication challenge (like MFA)

        This is equivalent to the sendMFACode function in the JavaScript SDK

        :param username: The username
        :type username: str
        :param challenge_name: The type of challenge
        :type challenge_name: str
        :param mfa_code: The verification code to respond with
        :type mfa_code: str
        :param challenge_response: The original challenge response
        :type challenge_response: Dict[str, Any]
        :return: Authentication result including tokens
        :rtype: Dict[str, Any]
        """
        auth_url = f"https://cognito-idp.{self.region}.amazonaws.com/"

        headers = {
            "X-Amz-Target": "AWSCognitoIdentityProviderService.RespondToAuthChallenge",
            "Content-Type": "application/x-amz-json-1.1",
        }

        payload = {
            "ChallengeName": challenge_name,
            "ClientId": self.client_id,
            "ChallengeResponses": {
                "USERNAME": username,
                "SMS_MFA_CODE": mfa_code,
                "SOFTWARE_TOKEN_MFA_CODE": mfa_code,
            },
            "Session": challenge_response.get("Session"),
        }

        self.log.info(f"Responding to auth challenge ({challenge_name}) with verification code")

        response = requests.post(auth_url, headers=headers, json=payload)

        if response.status_code != 200:
            error_msg = f"MFA verification failed with status {response.status_code}: {response.text}"
            self.log.error(f"ERROR: {error_msg}")
            raise AirflowException(error_msg)

        response_json = response.json()
        auth_result = response_json.get("AuthenticationResult", {})

        if not auth_result.get("IdToken"):
            error_msg = "MFA verification succeeded but no ID token was returned"
            self.log.error(f"ERROR: {error_msg}")
            raise AirflowException(error_msg)

        self.log.info("MFA verification successful")
        return auth_result

    def _authenticate_user_password(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate using USER_PASSWORD_AUTH flow

        :param username: FileMaker Cloud username
        :type username: str
        :param password: FileMaker Cloud password
        :type password: str
        :return: Authentication result
        :rtype: Dict[str, Any]
        """
        response = self.cognito_idp_client.initiate_auth(
            AuthFlow="USER_PASSWORD_AUTH",
            ClientId=self.client_id,
            AuthParameters={"USERNAME": username, "PASSWORD": password},
        )

        return response["AuthenticationResult"]

    def _authenticate_admin(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate using ADMIN_USER_PASSWORD_AUTH flow

        :param username: FileMaker Cloud username
        :type username: str
        :param password: FileMaker Cloud password
        :type password: str
        :return: Authentication result
        :rtype: Dict[str, Any]
        """
        response = self.cognito_idp_client.admin_initiate_auth(
            UserPoolId=self.user_pool_id,
            ClientId=self.client_id,
            AuthFlow="ADMIN_USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": username, "PASSWORD": password},
        )

        return response["AuthenticationResult"]

    def _authenticate_direct_api(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate using direct API calls to Cognito

        This is an alternative approach that uses direct HTTP requests

        :param username: FileMaker Cloud username
        :type username: str
        :param password: FileMaker Cloud password
        :type password: str
        :return: Authentication result
        :rtype: Dict[str, Any]
        """
        auth_url = f"https://cognito-idp.{self.region}.amazonaws.com/"

        headers = {
            "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
            "Content-Type": "application/x-amz-json-1.1",
        }

        payload = {
            "AuthFlow": "USER_PASSWORD_AUTH",
            "ClientId": self.client_id,
            "AuthParameters": {"USERNAME": username, "PASSWORD": password},
            "ClientMetadata": {},
        }

        self.log.info(f"Sending direct API auth request to {auth_url}")
        response = requests.post(auth_url, headers=headers, json=payload)

        self.log.info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            error_msg = f"Direct API authentication failed with status {response.status_code}: {response.text}"
            self.log.error(f"ERROR: {error_msg}")
            raise AirflowException(error_msg)

        response_json = response.json()

        return response_json.get("AuthenticationResult", {})

    def get_binary_field(self, endpoint, accept_format=None):
        """
        Get binary field value from OData API (images, attachments, etc.)

        :param endpoint: API endpoint for the binary field
        :param accept_format: Accept header format, default is 'application/octet-stream'
        :return: Binary content
        """
        # Get auth token
        token = self.get_token()

        # Set up headers with appropriate content type for binary data
        headers = {
            "Authorization": f"FMID {token}",
            "Accept": accept_format or "application/octet-stream",
        }

        # Make the request
        response = requests.get(endpoint, headers=headers)

        # Check for errors
        if response.status_code >= 400:
            raise Exception(f"OData API error retrieving binary field: {response.status_code} - {response.text}")

        # Return the binary content
        return response.content

    def _execute_request(self, endpoint, headers=None, method="GET", data=None):
        """
        Execute an HTTP request with proper error handling.

        :param endpoint: The endpoint URL
        :type endpoint: str
        :param headers: HTTP headers
        :type headers: Dict[str, str]
        :param method: HTTP method (GET, POST, etc.)
        :type method: str
        :param data: Request data for POST/PUT methods
        :type data: Any
        :return: Response object or content
        :rtype: Any
        """
        try:
            if method.upper() == "GET":
                response = requests.get(endpoint, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(endpoint, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(endpoint, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(endpoint, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            self.log.error(f"Request error: {str(e)}")
            raise AirflowException(f"Request failed: {str(e)}")
        except Exception as e:
            self.log.error(f"Unexpected error: {str(e)}")
            raise AirflowException(f"Unexpected error: {str(e)}")

    def _request_with_retry(
        self,
        endpoint,
        headers=None,
        method="GET",
        data=None,
        max_retries=3,
        retry_delay=1,
    ):
        try:
            # Try to execute the request with the retry logic
            return self._execute_request(endpoint, headers, method, data)
        except Exception as e:
            self.log.error(f"Error making request after {max_retries} retries: {str(e)}")
            raise AirflowException(f"Failed to execute request: {str(e)}")
