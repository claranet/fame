# Monitoring Azure's Backups

This repository hosts all stuff related to the monitoring of backup.

## Pre-requisites

  * An AppServiePlan with at least the free tier
  * Use a System Managed Identity with the Function App
  * Allow the Identity to be Reader on the whole subscription
  * A key vault with a secret named **sfx-org-token** which contains the SignalFx Organisation Token
  * The recovery vault **must** be associated to an Analytic Workspace

### Variables

  * **BACKUPS_CONFIG**: This variable must be in json format: `[{ "subscription_id": xxxxxx, "analytics_workspace_id": xxxxxx}, { "subscription_id": xxxxxx, "analytics_workspace_id": xxxxxx}]`
  * **KEY_VAULT_URL**: Url of the Keyvault in which the sfx-org-token is hosted
  * **WORKSPACE_ID**: Id of the backup log analytics workspace

## Functions
### report_iaas_backups

This function check for the backup of virtual machines on Azure. Its list all the VM's on the subscription and compare it with the VM's found in the Recovery Vault.

If the VM is not found in the Recovery Vault, we consider as a backup failure and will be reported to SignalFx with vault_name = Unknown

All backups jobs are reported from the Workspace Analytics of the recovery vault and the status is sent to SignalFx.


  

  