"""
FileMaker Cloud OData Connection class.
"""

from typing import Dict


class FileMakerConnection:
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
    ) -> None:
        self.host = host
        self.database = database
        self.username = username
        self.password = password

    def get_connection_params(self) -> Dict[str, str]:
        """
        Get connection parameters as a dictionary.

        :return: Connection parameters
        :rtype: Dict[str, str]
        """
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
        return f"{self.host}/fmi/odata/v4/{self.database}"
