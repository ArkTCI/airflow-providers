"""
FileMaker Cloud Provider for Apache Airflow.

This provider enables interaction with FileMaker Cloud's OData API,
including custom Cognito authentication.
"""

# Version managed by bump2version
__version__ = "2.4.2"


def get_provider_info():
    """
    Returns provider information for the FileMaker Cloud provider.

    :return: Provider information dictionary
    :rtype: dic
    """
    return {
        "package-name": "arktci-airflow-provider-filemaker",
        "name": "FileMaker Cloud",
        "description": "Provider for FileMaker Cloud OData API integration, including custom Cognito authentication.",
        "hook-class-names": ["airflow.providers.filemaker.hooks.filemaker.FileMakerHook"],
        "connection-types": [
            {
                "connection-type": "filemaker",
                "hook-class-name": "airflow.providers.filemaker.hooks.filemaker.FileMakerHook",
            }
        ],
        "versions": [__version__],
        "extra-links": [],
    }
