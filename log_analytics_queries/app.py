import atexit
import datetime
import glob
import logging
import os

import signalfx
from azure import functions as func
from dateutil.parser import parse

from libs import credentials
from libs import log_analytics


logger = logging.getLogger("log_analytics_queries")


def run_http():
    pass


def run_timer(timer: func.TimerRequest):
    if timer.past_due:
        logger.warning('The timer is past due!')
    run()


def run():
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    logger.info('Python timer trigger function ran at %s', utc_timestamp)
    sfx_token = os.environ.get('SFX_TOKEN')
    sfx_realm = os.environ.get('SFX_REALM', 'eu0')

    log_analytics_workspace_id = os.environ.get('LOG_ANALYTICS_WORKSPACE_GUID')
    creds = credentials.get_credentials()

    queries = {}
    for path in glob.glob(os.path.join(os.path.dirname(__file__), 'queries', '*.query')):
        metric = os.path.splitext(os.path.basename(path))[0]
        with open(path) as f:
            queries[metric] = f.read()

    sfx_clt = signalfx.SignalFx(api_endpoint=f'https://api.{sfx_realm}.signalfx.com',
                                ingest_endpoint=f'https://ingest.{sfx_realm}.signalfx.com',
                                stream_endpoint=f'https://stream.{sfx_realm}.signalfx.com'
                                )
    with sfx_clt.ingest(sfx_token) as sfx:
        atexit.register(sfx.stop)

        for metric, query in queries.items():
            metric_name = '.'.join(metric.split('.')[1:])
            metric_kind = metric.split('.')[0]

            sfx_values = []

            # TODO add logging
            data = log_analytics.run_query(query, log_analytics_workspace_id, creds)
            cols = [col['name'] for col in data['tables'][0]['columns']]
            # TODO have strict checking of those columns
            ix_timestamp = cols.index('timestamp')
            ix_metric_value = cols.index('metric_value')
            cols.pop(ix_timestamp)
            cols.pop(ix_metric_value - 1)
            for row in data['tables'][0]['rows']:
                timestamp = row.pop(ix_timestamp)
                metric_value = row.pop(ix_metric_value - 1)
                sfx_values.append({
                        'metric': metric_name,
                        'value': metric_value,
                        'timestamp': parse(timestamp).timestamp() * 1000,
                        # TODO add function tags as dimensions
                        'dimensions': dict(zip(cols, row))
                    })
            sfx.send(**{f"{metric_kind}s": sfx_values})


if __name__ == "__main__":
    sfx_logger = logging.getLogger('signalfx.ingest')
    sfx_logger.setLevel(logging.DEBUG)
    run()
