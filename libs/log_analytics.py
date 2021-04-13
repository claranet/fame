import requests


def run_query(query, log_analytics_workspace_id, credentials):
    token = credentials.get_token("https://api.loganalytics.io/").token

    query_headers = {'Authorization': str(f'Bearer {token}'), 'Content-Type': 'application/json'}

    url = f'https://api.loganalytics.io/v1/workspaces/{log_analytics_workspace_id}/query'
    params = {"query": query}
    result = requests.post(url, json=params, headers=query_headers)

    return result.json()
