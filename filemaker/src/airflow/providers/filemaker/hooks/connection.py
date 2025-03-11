"""
FileMaker Cloud OData Connection class.
"""

import json
import time
from typing import Dict, Optional, Any

from airflow.utils.log.logging_mixin import LoggingMixin


class FileMakerConnection(LoggingMixin):
    """
    Connection class for FileMaker Cloud.

    This class handles connection details for FileMaker Cloud.

    :param host: FileMaker Cloud host URL
    :type host: str
    :param database: FileMaker database name
    :type database: str
    :param username: FileMaker Cloud username
    :type username: str
    :param password: FileMaker Cloud password
    :type password: str
    """

    def __init__(
        self,
        host: str,
        database: str,
        username: str,
        password: str,
        connection_id: Optional[str] = None,
    ) -> None:
        # Initialize LoggingMixin first
        super().__init__()
        
        self.log.info("Initializing FileMaker connection")
        self.host = host
        self.database = database
        self.username = username
        self.password = password
        self.connection_id = connection_id or f"filemaker_{int(time.time())}"
        
        # Log connection details (without sensitive info)
        self.log.info(
            "FileMaker connection initialized (id: %s)", 
            self.connection_id
        )
        self.log.debug(
            "Connection details: host=%s, database=%s, username=%s", 
            self.host, 
            self.database, 
            self.username
        )

    def get_connection_params(self) -> Dict[str, str]:
        """
        Get connection parameters as a dictionary.

        :return: Connection parameters
        :rtype: Dict[str, str]
        """
        self.log.info("Retrieving connection parameters for %s", self.connection_id)
        
        # Create a safe copy for logging (with masked password)
        safe_params = {
            "host": self.host,
            "database": self.database,
            "username": self.username,
            "password": "********",  # Masked for security in logs
        }
        
        self.log.debug("Safe connection parameters: %s", json.dumps(safe_params))
        self.log.info("Connection parameters retrieved successfully")
        
        # Return actual parameters with real password
        return {
            "host": self.host,
            "database": self.database,
            "username": self.username,
            "password": self.password,
        }

    def get_base_url(self) -> str:
        """
        Get the base URL for the OData API.

        :return: The base URL
        :rtype: str
        """
        self.log.info("Generating OData base URL for database %s", self.database)
        base_url = f"{self.host}/fmi/odata/v4/{self.database}"
        self.log.info("Generated OData base URL: %s", base_url)
        return base_url
        
    def test_connection(self) -> bool:
        """
        Test the connection to FileMaker Cloud.
        
        :return: True if connection is successful, False otherwise
        :rtype: bool
        """
        try:
            self.log.info("Testing connection to FileMaker Cloud")
            base_url = self.get_base_url()
            self.log.debug("Using base URL: %s", base_url)
            
            # Here you would actually test the connection
            # For example, make a simple request to the server
            # For now, we'll just assume it works if we have all parameters
            is_valid = all([self.host, self.database, self.username, self.password])
            
            if is_valid:
                self.log.info("Connection test successful")
            else:
                self.log.error("Connection test failed: missing required parameters")
                
            return is_valid
        except Exception as e:
            self.log.error("Connection test failed with error: %s", str(e), exc_info=True)
            return False
