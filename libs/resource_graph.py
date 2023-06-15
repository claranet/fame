"""Azure Resource Graph management."""
import requests


class ResourceGraphException(Exception):
    """Specific Exception."""

    pass


def run_query(query, subscription_id, credentials):
    """
    Run a query on the Resource graph.

    :param query: Kusto query to run
    :param subscription_id: GUID of subscription
    :param credentials: Azure credentials
    :return: a dict with the result of the query
    """
    token = credentials.get_token("https://management.azure.com//.default").token

    query_headers = {
        "Authorization": str(f"Bearer {token}"),
        "Content-Type": "application/json",
    }

    url = "https://management.azure.com/providers/Microsoft.ResourceGraph/resources?api-version=2020-04-01-preview"
    params = {"query": query, "subscriptions": [subscription_id]}
    result = requests.post(url, json=params, headers=query_headers)

    if result.status_code != 200:
        try:
            message = result.json()["error"]["message"]
        except:  # noqa E722
            message = result.text
        raise ResourceGraphException(f"Error while querying Resource Graph: {message}")

    res = result.json()
    if "data" not in res:
        return []
    return res["data"]
