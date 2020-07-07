import logging
import os
from typing import List, Tuple

import requests
import signalfx
from azure.identity import ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient
from azure.loganalytics.models import QueryBody
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import VirtualMachine

from ..shared.cred_wrapper import CredentialWrapper

QUERY = 'AddonAzureBackupJobs | where TimeGenerated > ago(1d) | summarize arg_max(TimeGenerated,*) by JobUniqueId'


def get_token_from_keyvault(secret: str) -> str:
    """
    Return the value of a secret
    :param secret: Name of the secret to retrieve
    :type secret: str
    :return: value of the secret
    :rtype: str
    """

    managed_identity_client_id = os.environ.get("MANAGED_IDENTITY_CLIENT_ID")
    key_vault_url = os.environ.get("KEY_VAULT_URL")
    logging.info(f'Managed identity client id: {managed_identity_client_id}')
    logging.info(f'Key vault url: {key_vault_url}')

    credentials = ManagedIdentityCredential(client_id=managed_identity_client_id)
    key_vault_client = SecretClient(vault_url=key_vault_url, credential=credentials)
    secret = key_vault_client.get_secret(secret)

    return secret.value


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


def query_workspace(log_analytics_workspace_id: str, query_body: QueryBody) -> dict:
    """
    Launch a query to a LogAnalytics Workspace and return the result
    :param log_analytics_workspace_id: Id of the workspace to query
    :type log_analytics_workspace_id: str
    :param query_body: The query to launch
    :type query_body: QueryBody
    :return: The query result as a json
    :rtype: str

    """

    managed_identity_client_id = os.environ.get("MANAGED_IDENTITY_CLIENT_ID")
    credentials = ManagedIdentityCredential(client_id=managed_identity_client_id,
                                            resource="https://api.loganalytics.io/")
    token = credentials.get_token("https://api.loganalytics.io/").token

    query_headers = {'Authorization': str(f'Bearer {token}'), 'Content-Type': 'application/json'}

    url = f'https://api.loganalytics.io/v1/workspaces/{log_analytics_workspace_id}/query'
    params = {"query": query_body}
    result = requests.post(url, json=params, headers=query_headers, verify=False)

    return result.json()


def not_backuped_vms(vms: List[VirtualMachine], backups_result: List[List[str]]) -> List[dict]:
    """
    Check if vms are in the list of backuped vms
    :param vms: list of vms
    :type vms: List[VirtualMachine]
    :param backups_result: List of backuped vms
    :type backups_result: List[List[str]]
    :return: List of not backuped vms identified by resource_group_name and vm_name
    :rtype: list
    """

    backuped_vms_name = [f'{";".join(x[8].split(";")[-2:]).lower()}' for x in backups_result]
    vms_list = [f'{x.id.split("/")[4].lower()};{x.name.lower()}' for x in vms]

    not_backuped = [{"rg": x.split(";")[-2], 'vm_name': x.split(";")[-1]} for x in vms_list if
                    x not in backuped_vms_name]
    return not_backuped


def failed_and_success_backups(backups_result: List[List[str]]) -> Tuple[List[str], List[str]]:
    """
    Check for failed and successful backups jobs and return vms name with RG
    depending their status.
    :param backups_result: List of backups
    :return: List of failed jobs and List of successfull jobs
    :rtype: Tuple[List[str], List[str]]
    """

    failed_jobs = [{'rg': x[8].split(";")[-2].lower(), 'vm_name': x[8].split(";")[-1].lower(),
                    'vault_name': x[4].split('/')[-1].lower()} for x in backups_result if x[13] != "Success"]
    successful_jobs = [{'rg': x[8].split(";")[-2].lower(), 'vm_name': x[8].split(";")[-1].lower(),
                        'vault_name': x[4].split('/')[-1].lower()} for x in backups_result if x[13] == "Success"]

    return failed_jobs, successful_jobs


def send_backup_status_to_sfx(datas: dict, org_token: str, sfx_realm: str = 'eu0') -> None:
    """
    Send backup status to SFX. If a VM is not found in the Backup Vault
    the backup for this VM is considered as failed with vault_name to Unknown.
    :param datas: Datas to send to SFX
    :type datas: dict
    :param org_token: SignalFx Organisation token
    :type org_token: str
    :param sfx_realm: SignalFx realm. Default to eu0
    :type sfx_realm: str
    :return: None
    """

    metric_name = "azure.backups"

    sfx = signalfx.SignalFx(api_endpoint=f'https://api.{sfx_realm}.signalfx.com',
                            ingest_endpoint=f'https://ingest.{sfx_realm}.signalfx.com',
                            stream_endpoint=f'https://stream.{sfx_realm}.signalfx.com'
                            )

    ingest = sfx.ingest(org_token)

    gauges_list = [{'metric': metric_name,
                    'value': 0,
                    'dimensions': {'vault_name': x.get('vault_name', 'Unknown'),
                                   'vm_name': x.get('vm_name', ''),
                                   'resource_group': x.get('rg', '')
                                   }
                    } for x in datas.get('success')]
    gauges_list = gauges_list + [{'metric': metric_name,
                                  'value': 1,
                                  'dimensions': {'vault_name': x.get('vault_name', 'Unknown'),
                                                 'vm_name': x.get('vm_name', ''),
                                                 'resource_group': x.get('rg', '')
                                                 }
                                  } for x in datas['failed']]

    gauges_list = gauges_list + [{'metric': metric_name,
                                  'value': 1,
                                  'dimensions': {'vault_name': x.get('vault_name', 'Unknown'),
                                                 'vm_name': x.get('vm_name', ''),
                                                 'resource_group': x.get('rg', '')
                                                 }
                                  } for x in datas['not_backuped']
                                 ]

    try:
        logging.info("Send data to SignalFX")
        ingest.send(
            gauges=gauges_list
        )
    finally:
        ingest.stop()


def main(req):
    logger = logging.getLogger()

    org_token = get_token_from_keyvault('sfx-org-token')
    subscription_id = os.environ.get('SUBSCRIPTION_ID', None)
    workspace_id = os.environ.get('WORKSPACE_ID', None)

    logger.info('Get Analytic query')
    rez = query_workspace(workspace_id, QUERY)

    backups_list = rez['tables'][0]['rows']

    vms_list = get_sub_vms_list(subscription_id)
    not_backuped = not_backuped_vms(vms_list, backups_list)
    failed, success = failed_and_success_backups(backups_list)

    bkp_datas = {'success': success,
                 'failed': failed,
                 'not_backuped': not_backuped
                 }

    send_backup_status_to_sfx(bkp_datas, org_token)

# if __name__ == "__main__":
#     logger = logging.getLogger()
#     logger.setLevel(logging.DEBUG)
#
#     ch = logging.StreamHandler()
#     logger.addHandler(ch)
#
#     backups_list = list()
#     ORG_TOKEN = os.environ.get("SFX_ORG_TOKEN")
#
#     with open('queries/backups_jobs.txt', 'r') as jobs:
#         query = jobs.read()
#         # Claranet Sandbox
#         rez = query_workspace('499bbc6c-d927-488d-8e6d-a463319d78fe', '261efbf6-6481-4c02-885f-d67f1ddae863', query)
#
#         # L'occitane
#         # rez = query_workspace('94dbb400-32e0-4301-bf7c-305c7b917412', 'eb9e07d0-aa86-4dbe-8c97-afd868b52847', query)
#
#         # LVM TRACK TRACE PREPROD
#         # rez = query_workspace('52c23d98-cec4-46bb-b4db-aa2a05e65f87', 'a70a49f4-53d6-4f4a-a111-69c4eec3e7f6', query)
#
#         backups_list = rez.tables[0].rows
#
#     vms_list = get_sub_vms_list()
#     not_backuped = not_backuped_vms(vms_list, backups_list)
#     failed, success = failed_and_success_backups(backups_list)
#
#     bkp_datas = {'success': success,
#                  'failed': failed,
#                  'not_backuped': not_backuped
#                  }
#
#     send_backup_status_to_sfx(bkp_datas, ORG_TOKEN)
