"""Azure Log Analytics management."""

import logging

import requests

logger = logging.getLogger("log_queries")


class LogAnalyticsException(Exception):
    """Specific Exception."""

    pass


def run_query(query, log_analytics_workspace_id, credentials):
    """
    Run a query within a given Log Analytics Workspace.

    :param query: Kusto query to run
    :param log_analytics_workspace_id: GUID of the Log Analytics workspace
    :param credentials: Azure credentials
    :return: a dict with the result of the query
    """
    token = credentials.get_token("https://api.loganalytics.io/.default").token

    query_headers = {
        "Authorization": str(f"Bearer {token}"),
        "Content-Type": "application/json",
    }

    url = (
        f"https://api.loganalytics.io/v1/workspaces/{log_analytics_workspace_id}/query"
    )
    params = {"query": query}
    result = requests.post(url, json=params, headers=query_headers)

    if result.status_code != 200:
        logger.error(
            f"Error while querying Log Analytics {log_analytics_workspace_id}: {result.status_code} - {result.text}"
        )
        try:
            message = result.json()["error"]["message"]
        except Exception:
            message = result.text
        raise LogAnalyticsException(
            f"Error while querying Log Analytics {log_analytics_workspace_id}: {message}"
        )

    res = result.json()
    if "tables" not in res:
        return {}
    return res["tables"][0]
