from azure.identity import DefaultAzureCredential


def get_credentials():
    return DefaultAzureCredential(exclude_shared_token_cache_credential=True)
