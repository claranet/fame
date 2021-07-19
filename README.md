# Fame - Function for Azure Monitoring Extension

This repository hosts an Azure Function App Python code in order to run Log Analytics queries and send result to 
[Splunk Observability](https://www.splunk.com/en_us/observability.html) (formerly SignalFx). 


## Pre-requisites

  * A Python 3.8 [Azure Function App](https://docs.microsoft.com/en-us/azure/azure-functions/functions-overview) 
  * A [Log Analytics Workspace](https://docs.microsoft.com/en-us/azure/azure-monitor/logs/log-analytics-overview)
    with resources [Diagnostic Settings](https://docs.microsoft.com/en-us/azure/azure-monitor/essentials/diagnostic-settings?tabs=CMD)
    linked to it
  * A [Table Storage](https://docs.microsoft.com/en-us/azure/storage/tables/table-storage-overview) containing the queries.
  * Function [Managed Identity](https://docs.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/overview)
    or Azure [Service Principal](https://docs.microsoft.com/en-us/azure/active-directory/develop/app-objects-and-service-principals#service-principal-object)
    with at least `Log Analytics Reader` right on the Log Analytics Workspace and `Reader and Data Access` on the Storage Account if storage key is not provided.
  * A [Splunk Observability](https://www.observability.splunk.com/en_us/infrastructure-monitoring.html) account and its 
    associated [ingest Token](https://dev.splunk.com/observability/docs/administration/authtokens/#Organization-access-tokens)


### Variables

  * **QUERIES_STORAGE_ACCOUNT_NAME** (required): The name of the Storage Account containing the table with the queries
  * **QUERIES_STORAGE_ACCOUNT_KEY** (required): The key to access the Storage Account containing the table with the queries, will try to fetch it if empty
  * **QUERIES_STORAGE_TABLE_NAME** (optional, defaults to `LogQueries`): The name of the table in the Storage Account with the queries
  * **SFX_TOKEN** (required): The Splunk Observability token for metric sending
  * **SFX_REALM** (optional, defaults to `eu0`): Splunk realm (region) to use for metric sending  
  * **LOG_ANALYTICS_WORKSPACE_GUID** (required): ID of the Log Analytics Workspace
  * **LOG_LEVEL** (optional, defaults to `INFO`): Logging level
  * **SFX_EXTRA_DIMENSIONS** (optional): Extra dimensions to send to Splunk Observability. 
    Example: `env=prod,sfx_monitored=true`
  * **AZURE_CLIENT_ID** (optional): Azure Service Principal ID if Service Principal authentication is used
  * **AZURE_TENANT_ID** (optional): Azure Tenant ID if Service Principal authentication is used
  * **AZURE_CLIENT_SECRET** (optional): Azure Service Principal secret key if Service Principal authentication is used


## How it works

The function runs all the queries stored in the associated Table Storage every minute within the given 
Log Analytics Workspace and send the result to Splunk Observability.

Each query specifies the value of the metric and its associated time. Every column in the query is sent as metric 
dimension along with the defined `EXTRA_DIMENSIONS` variable. 


### Table storage format

The records in the Table STorage must have the following columns:
 * **MetricName**: Name of the metric to send to Splunk Observability
 * **MetricType**: Type of metric, can be gauge, counter or cumulative_counter 
   (See [https://docs.signalfx.com/en/latest/metrics-metadata/metric-types.html](https://docs.signalfx.com/en/latest/metrics-metadata/metric-types.html))
 * **Query**: Query to run on the Log Analytics Workspace 
   (See [https://docs.microsoft.com/en-us/azure/azure-monitor/logs/get-started-queries](https://docs.microsoft.com/en-us/azure/azure-monitor/logs/get-started-queries))


### Log queries requirements

The query must contain the columns `metric_value` with a metric value and `timespan` with the datetime of the metric to send.
The others columns are treated as dimensions for the metric.

## How to deploy

You can use [Zip deployment](https://docs.microsoft.com/en-us/azure/azure-functions/deployment-zip-push), 
[Azure Function Core Tools](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local#publish) 
or any other Azure deployment method to deploy this application.
