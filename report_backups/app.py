import logging
import os
import sys
from os import path
from typing import List, Tuple, Union

sys.path.append(path.dirname(path.dirname(__file__)))

from azure.mgmt.compute.models import VirtualMachine
from azure.mgmt.storage.models import StorageAccount
from azure import functions as func
from shared.keyvault.secrets import get_secret_from_keyvault
from shared.loganalytics.workspace import query
from shared.vms import get_sub_vms_list
from shared.sfx.send import send_status_to_sfx
from shared.storage import get_sub_storages
import datetime
from collections import namedtuple

QUERY = 'AddonAzureBackupJobs | where TimeGenerated > ago(1d) | where JobOperation == "Backup" | summarize arg_max(TimeGenerated,*) by JobUniqueId'


def not_backuped_resources(azobjects: List[Union[VirtualMachine, StorageAccount]], backups_result: List[namedtuple]) -> \
        List[dict]:
    """
    Check if vms are in the list of backuped vms
    :param vms: List of Azure Objects
    :type vms: List[VirtualMachine, StorageAccount]
    :param backups_result: List of backuped vms
    :type backups_result: List[List[str]]
    :return: List of not backuped vms identified by resource_group_name and vm_name
    :rtype: list
    """

    backuped_resources_name = [f'{";".join(x.BackupItemUniqueId.split(";")[3:5]).lower()}' for x in backups_result]
    azobjects_list = [f'{x.id.split("/")[4].lower()};{x.name.lower()}' for x in azobjects]

    not_backuped = [{"rg": x.split(";")[-2], 'resource_name': x.split(";")[-1]} for x in azobjects_list if
                    x not in backuped_resources_name]
    return not_backuped


def failed_and_success_backups(backups_result: List[namedtuple]) -> Tuple[List[str], List[str]]:
    """
    Check for failed and successful backups jobs and return vms name with RG
    depending their status.
    :param backups_result: List of backups
    :return: List of failed jobs and List of successfull jobs
    :rtype: Tuple[List[str], List[str]]
    """

    failed_jobs = [{'rg': x.BackupItemUniqueId.split(";")[3].lower(),
                    'resource_name': x.BackupItemUniqueId.split(";")[4].lower(),
                    'vault_name': x.ResourceId.split('/')[-1].lower()} for x in backups_result if
                   x.JobFailureCode != "Success"]
    successful_jobs = [{'rg': x.BackupItemUniqueId.split(";")[3].lower(),
                        'resource_name': x.BackupItemUniqueId.split(";")[4].lower(),
                        'vault_name': x.ResourceId.split('/')[-1].lower()} for x in backups_result if
                       x.JobFailureCode == "Success"]

    return failed_jobs, successful_jobs


def main(timer: func.TimerRequest):
    logger = logging.getLogger("report_backups")
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if timer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)
    org_token = get_secret_from_keyvault('sfx-org-token')
    subscription_id = os.environ.get('AZURE_SUBSCRIPTION_ID', None)
    workspace_id = os.environ.get('WORKSPACE_ID', None)

    logger.info('Get Analytic query')
    rez = query(workspace_id, QUERY)

    result_headers = [x['name'] for x in rez['tables'][0]['columns']]
    backups_list = rez['tables'][0]['rows']

    # Create a named tuple to avoid parsing list by list indexes
    backups_named_list = list()
    Row = namedtuple('Row', result_headers)
    [backups_named_list.append(Row(*x)) for x in backups_list]

    vms_list = get_sub_vms_list(subscription_id)
    storages_list = get_sub_storages(subscription_id)
    azure_objects_list = vms_list + storages_list

    logger.debug('Storages List: %s', storages_list)
    not_backuped = not_backuped_resources(azure_objects_list, backups_named_list)

    failed, success = failed_and_success_backups(backups_named_list)

    bkp_datas = {'success': success,
                 'failed': failed,
                 'not_backuped': not_backuped
                 }

    metric_name = "azure.backups"

    gauges_list = [{'metric': metric_name,
                    'value': 0,
                    'dimensions': {'vault_name': x.get('vault_name', 'Unknown'),
                                   'resource_name': x.get('resource_name', ''),
                                   'resource_group': x.get('rg', '')
                                   }
                    } for x in bkp_datas.get('success')]

    gauges_list = gauges_list + [{'metric': metric_name,
                                  'value': 1,
                                  'dimensions': {'vault_name': x.get('vault_name', 'Unknown'),
                                                 'resource_name': x.get('resource_name', ''),
                                                 'resource_group': x.get('rg', '')
                                                 }
                                  } for x in bkp_datas.get('failed')]

    gauges_list = gauges_list + [{'metric': metric_name,
                                  'value': 1,
                                  'dimensions': {'vault_name': x.get('vault_name', 'Unknown'),
                                                 'resource_name': x.get('resource_name', ''),
                                                 'resource_group': x.get('rg', '')
                                                 }
                                  } for x in bkp_datas.get('not_backuped')
                                 ]

    send_status_to_sfx(org_token, gauges=gauges_list)
