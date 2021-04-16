# Claranet Log Analytics queries monitoring

This repository hosts an Azure Function App Python code in order to run Log Analytics queries and send result to 
Splunk Observability. 

## Pre-requisites

  * A Python 3.8 [Azure Function App](https://docs.microsoft.com/en-us/azure/azure-functions/functions-overview) 
  * A [Log Analytics Workspace](https://docs.microsoft.com/en-us/azure/azure-monitor/logs/log-analytics-overview)
    with resources [Diagnostic Settings](https://docs.microsoft.com/en-us/azure/azure-monitor/essentials/diagnostic-settings?tabs=CMD)
    linked to it
  * Function [Managed Identity](https://docs.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/overview)
    or Azure [Service Principal](https://docs.microsoft.com/en-us/azure/active-directory/develop/app-objects-and-service-principals#service-principal-object)
    with at least `Log Analytics Reader` right on the Log Analytics Workspace
  * A [Splunk Observability](https://www.observability.splunk.com/en_us/infrastructure-monitoring.html) account and its 
    associated [ingest Token](https://dev.splunk.com/observability/docs/administration/authtokens/#Organization-access-tokens)

### Variables

  * **SFX_TOKEN** (required): The Splunk Observability token for metric sending
  * **SFX_REALM** (optional, defaults to `eu0`): Splunk realm (region) to use for metric sending  
  * **LOG_ANALYTICS_WORKSPACE_GUID** (required): ID of the Log Analytics Workspace
  * **LOG_LEVEL** (optional, defaults to `INFO`): Logging level
  * **SFX_EXTRA_DIMENSIONS** (optional): Extra dimensions to send to SignalFx. 
    Example: `env=prod,sfx_monitored=true`
  * **AZURE_CLIENT_ID** (optional): Azure Service Principal ID if Service Principal authentication is used
  * **AZURE_TENANT_ID** (optional): Azure Tenant ID if Service Principal authentication is used
  * **AZURE_CLIENT_SECRET** (optional): Azure Service Principal secret key if Service Principal authentication is used


## How it works

The function run all the queries in the `log_analtics_queries/queries` directory every minute and send the result to 
Splunk Observability.
Each query specific the value of the metric and its associated time. Every column in the query is sent as metric 
dimension along with the defined `EXTRA_DIMENSIONS` variable. 

## Supported metrics

### Application Gateway instances

See [application_gateway_instances.yaml](log_analytics_queries/queries/application_gateway_instances.yaml)

Number of Application Gateway instances over time.

Dimensions: azure_resource_name, azure_resource_group_name, subscription_id

### Virtual Machines Backup

See [virtual_machines_backup.yaml](log_analytics_queries/queries/virtual_machines_backup.yaml)

Status of the latest  VVirtual Machine backup.

Dimensions: subscription_id, recovery_vault_name, azure_resource_group_name, azure_resource_name

### Virtual Network Gateway successful IKE diagnostics

See [vpn_successful_ike_diags.yaml](log_analytics_queries/queries/vpn_successful_ike_diags.yaml)

Number of Virtual Network Gateway successful IKE diagnostics messages over time

Dimensions: azure_resource_name, azure_resource_group_name, subscription_id

## How to add new metrics

Take a look at the sample file: [example.yaml.sample](log_analytics_queries/queries/example.yaml.sample)

Add a `yaml` file in the `log_analytics_queries/queries` file base on this example:

```yaml
---
metric_name: claranet.azure.application_gateway.instances
metric_type: gauge
query: |
    AzureDiagnostics
    | where ResourceType == "APPLICATIONGATEWAYS" and OperationName == "ApplicationGatewayAccess"
    | summarize metric_value=dcount(instanceId_s) by timestamp=bin(TimeGenerated, 1m), azure_resource_name=Resource, azure_resource_group_name=ResourceGroup, subscription_id=SubscriptionId

```

The file must contain the metric name, the [Splunk metric type](https://docs.signalfx.com/en/latest/metrics-metadata/metric-types.html) and a Log Analytics query.

The query must contain the columns `metric_value` with a metric value and `timespan` with the datetime of the metric to send.
The others columns are treated as dimensions of the metric.
