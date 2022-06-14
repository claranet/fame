"""
Log Analytics queries function.

Azure Function App function for running queries along a Log Analytics Workspace
and send the result to Splunk Observability.
"""
import atexit
import datetime
import logging
import os

import signalfx
from azure import functions as func
from azure.data.tables import TableClient
from dateutil.parser import parse

from libs import credentials
from libs import log_analytics
from libs.log_analytics import LogAnalyticsException

logger = logging.getLogger("log_analytics_queries")
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logger.setLevel(log_level)
sh = logging.StreamHandler()
sh.setLevel(log_level)
logger.addHandler(sh)

sfx_logger = logging.getLogger("signalfx.ingest")
sfx_logger.setLevel(log_level)
sfx_logger.addHandler(sh)


def run_http():
    """
    Azure Function App HTTP trigger function.

    :return: None
    """
    logger.info("Triggering with HTTP endpoint")

    run()


def run_timer(timer: func.TimerRequest):
    """
    Azure Function App Timer trigger function.

    :param timer: Azure Timer trigger
    :return: None
    """
    if timer.past_due:
        logger.warning("The timer is past due!")

    utc_timestamp = (
        datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    )

    logger.info("Python timer trigger function ran at %s", utc_timestamp)

    run()


def run():
    """
    Run the job.

    :return: None
    """
    logger.info("Starting job")

    sfx_token = os.environ.get("SFX_TOKEN")
    if not sfx_token:
        raise ValueError("Environment variable SFX_TOKEN not set")
    sfx_realm = os.environ.get("SFX_REALM", "eu0")
    logging.info(f"SignalFx realm: {sfx_realm}")

    log_analytics_workspace_id = os.environ.get("LOG_ANALYTICS_WORKSPACE_GUID")
    if not log_analytics_workspace_id:
        raise ValueError("Environment variable LOG_ANALYTICS_WORKSPACE_GUID not set")
    logging.info(f"Log Analytics workspace id: {log_analytics_workspace_id}")

    creds = credentials.get_credentials()

    extra_dimensions = {
        couple.split("=")[0]: couple.split("=")[1]
        for couple in os.environ.get("SFX_EXTRA_DIMENSIONS", "").split(",")
        if couple != ""
    }
    logging.info(f"Extra signalFx dimensions: {extra_dimensions}")

    storage_name = os.getenv("QUERIES_STORAGE_ACCOUNT_NAME")
    storage_key = os.getenv("QUERIES_STORAGE_ACCOUNT_KEY")

    if not storage_name and not storage_key:
        storage_connection_string = os.getenv("AzureWebJobsStorage")
        if not storage_connection_string:
            raise ValueError(
                "Either QUERIES_STORAGE_ACCOUNT_NAME and QUERIES_STORAGE_ACCOUNT_KEY or "
                "AzureWebJobsStorage environment variables must be set"
            )
    else:
        storage_connection_string = (
            f"DefaultEndpointsProtocol=https;AccountName={storage_name};"
            f"AccountKey={storage_key};"
            f"EndpointSuffix=core.windows.net"
        )

    table_name = os.getenv("QUERIES_STORAGE_TABLE_NAME") or "LogQueries"
    table_client = TableClient.from_connection_string(
        storage_connection_string, table_name=table_name
    )
    queries_config = []
    for data in table_client.query_entities(""):
        if (
            not data.get("MetricName", False)
            or not data.get("MetricType", False)
            or not data.get("Query", False)
        ):
            raise ValueError(
                f"Table {table_name} does not contain columns "
                f'"MetricName", "MetricType" and "Query'
            )
        queries_config.append(data)

    sfx_clt = signalfx.SignalFx(
        api_endpoint=f"https://api.{sfx_realm}.signalfx.com",
        ingest_endpoint=f"https://ingest.{sfx_realm}.signalfx.com",
        stream_endpoint=f"https://stream.{sfx_realm}.signalfx.com",
    )
    with sfx_clt.ingest(sfx_token) as sfx:
        atexit.register(sfx.stop)

        for query_data in queries_config:
            sfx_values = []
            metric_name = query_data.get("MetricName")
            logger.info(f"Querying and sending metric {metric_name}")

            logger.debug(f"Executing query f{query_data['Query']}")
            try:
                data = log_analytics.run_query(
                    query_data["Query"], log_analytics_workspace_id, creds
                )
            except LogAnalyticsException:
                logger.exception(f"Error while running query for {metric_name}")
                continue

            if "tables" not in data:
                logger.warning(f"No result for the query {metric_name}")
                continue
            logger.debug("Found data for query")

            dimensions = [col["name"] for col in data["tables"][0]["columns"]]
            try:
                ix_timestamp = dimensions.index("timestamp")
                ix_metric_value = dimensions.index("metric_value")
            except ValueError:
                raise ValueError(
                    'Columns "timestamp" and "metric_value" must exist in the query results'
                )
            logger.debug("Found `timestamp` and `metric_value` columns")

            # Remove timestamp & metrics_value from dimensions
            dimensions.pop(ix_timestamp)
            dimensions.pop(ix_metric_value - 1)

            for row in data["tables"][0]["rows"]:
                timestamp = row.pop(ix_timestamp)
                metric_value = row.pop(ix_metric_value - 1)
                metric_dimensions = {
                    **dict(zip(dimensions, row)),
                    **extra_dimensions,
                }
                sfx_values.append(
                    {
                        "metric": metric_name,
                        "value": metric_value,
                        "timestamp": parse(timestamp).timestamp() * 1000,
                        "dimensions": metric_dimensions,
                    }
                )
                logger.debug(
                    f"Metric {metric_name} value: {parse(timestamp).isoformat()} - {metric_value}"
                )
                logger.debug(f"Metric {metric_name} dimensions: {metric_dimensions}")
            sfx.send(**{f"{query_data.get('MetricType')}s": sfx_values})
            logger.info(f"Metric {query_data['MetricName']} successfully sent")


if __name__ == "__main__":
    run()
