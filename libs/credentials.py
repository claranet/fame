"""Azure Credentials management."""

from azure.identity import DefaultAzureCredential


def get_credentials():
    """
    Return the Azure Credentials to use with Azure APIs.

    :return: Azure credentials
    """
    return DefaultAzureCredential(exclude_shared_token_cache_credential=True)
