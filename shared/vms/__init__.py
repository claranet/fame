import logging
from typing import List

from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import VirtualMachine

from ..cred_wrapper import CredentialWrapper

logging.getLogger(__name__)


def get_sub_vms_list(subscription_id: str) -> List[VirtualMachine]:
    """
    Get all vms from the subscription
    :param subscription_id: Id of the subscription
    :type subscription_id: str
    :return: List of VMs
    """

    credentials = CredentialWrapper()
    cli = ComputeManagementClient(credentials, subscription_id)
    all_vms = cli.virtual_machines.list_all()
    vm_list = list()
    for vm in all_vms:
        vm_list.append(vm)

    return vm_list
