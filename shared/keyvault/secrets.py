import logging
import os

from azure.identity import ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient

logging.getLogger(__name__)


def get_secret_from_keyvault(secret_name: str) -> str:
    """
    Return the value of a secret
    :param secret_name: Name of the secret to retrieve
    :type secret_name: str
    :return: value of the secret
    :rtype: str
    """

    managed_identity_client_id = os.environ.get("MANAGED_IDENTITY_CLIENT_ID")
    key_vault_url = os.environ.get("KEY_VAULT_URL")
    logging.info(f'Managed identity client id: {managed_identity_client_id}')
    logging.info(f'Key vault url: {key_vault_url}')

    credentials = ManagedIdentityCredential(client_id=managed_identity_client_id)
    key_vault_client = SecretClient(vault_url=key_vault_url, credential=credentials)
    secret_name = key_vault_client.get_secret(secret_name)

    return secret_name.value
