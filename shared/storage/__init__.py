import logging
from typing import List

from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import StorageAccount

from ..cred_wrapper import CredentialWrapper

logger = logging.getLogger("shared.storage")


def get_sub_storages(subscription_id: str) -> List[StorageAccount]:
    """
    Get list of subscription storage accounts
    :param subscription_id: Id of the subscription
    :type subscription_id: str
    :return: List of all storages accounts in the subscription
    :rtype: List[StorageAccounts]
    """

    credentials = CredentialWrapper()
    cli = StorageManagementClient(credentials, subscription_id)
    all_stor = cli.storage_accounts.list()

    stor_list = list()
    for x in all_stor:
        stor_list.append(x)
    logger.debug('Full storages list: %s', stor_list)
    return stor_list
