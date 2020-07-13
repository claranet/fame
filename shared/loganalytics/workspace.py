import logging
import os

import requests
from azure.identity import ManagedIdentityCredential
from azure.loganalytics.models import QueryBody

logging.getLogger(__name__)


def query(log_analytics_workspace_id: str, query_body: QueryBody) -> dict:
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
    result = requests.post(url, json=params, headers=query_headers)

    return result.json()
