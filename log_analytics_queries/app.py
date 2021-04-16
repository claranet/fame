import atexit
import datetime
import glob
import logging
import os

import signalfx
import yaml
from azure import functions as func
from dateutil.parser import parse

from libs import credentials
from libs import log_analytics


logger = logging.getLogger("log_analytics_queries")
log_level = logging.getLevelName(os.environ.get('LOG_LEVEL', logging.INFO))
logger.setLevel(log_level)
sh = logging.StreamHandler()
sh.setLevel(log_level)
logger.addHandler(sh)

sfx_logger = logging.getLogger('signalfx.ingest')
sfx_logger.setLevel(log_level)
sfx_logger.addHandler(sh)


def run_http():
    pass


def run_timer(timer: func.TimerRequest):
    if timer.past_due:
        logger.warning('The timer is past due!')

    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    logger.info('Python timer trigger function ran at %s', utc_timestamp)

    run()


def run():
    logger.info("Starting job")

    sfx_token = os.environ.get('SFX_TOKEN')
    if not sfx_token:
        raise ValueError("Environment variable SFX_TOKEN not set")
    sfx_realm = os.environ.get('SFX_REALM', 'eu0')
    logging.info(f"SignalFx realm: {sfx_realm}")

    log_analytics_workspace_id = os.environ.get('LOG_ANALYTICS_WORKSPACE_GUID')
    logging.info(f"Log Analytics workspace id: {log_analytics_workspace_id}")

    creds = credentials.get_credentials()

    extra_dimensions = {couple.split("=")[0]: couple.split("=")[1]
                        for couple in os.environ.get('SFX_EXTRA_DIMENSIONS', '').split(",")
                        }
    logging.info(f"Extra signalFx dimensions: {extra_dimensions}")

    queries_config = []
    for path in glob.glob(os.path.join(os.path.dirname(__file__), 'queries', '*.yaml')):
        with open(path) as f:
            data = yaml.safe_load(f)
            if not data.get('metric_name', False) or not data.get('metric_type', False) or not data.get('query', False):
                raise ValueError(f'Configuration file f{os.path.basename(path)} does not contain properties '
                                 f'"metric_name", "metric_type" and "query')
            queries_config.append(data)

    sfx_clt = signalfx.SignalFx(api_endpoint=f'https://api.{sfx_realm}.signalfx.com',
                                ingest_endpoint=f'https://ingest.{sfx_realm}.signalfx.com',
                                stream_endpoint=f'https://stream.{sfx_realm}.signalfx.com'
                                )
    with sfx_clt.ingest(sfx_token) as sfx:
        atexit.register(sfx.stop)

        for query_data in queries_config:
            sfx_values = []
            logger.info(f"Querying and sending metric {query_data['metric_name']}")

            logger.debug(f"Executing query f{query_data['query']}")
            data = log_analytics.run_query(query_data['query'], log_analytics_workspace_id, creds)
            cols = [col['name'] for col in data['tables'][0]['columns']]
            try:
                ix_timestamp = cols.index('timestamp')
                ix_metric_value = cols.index('metric_value')
            except ValueError:
                raise ValueError('Columns "timestamp" and "metric_value" must exist in the query results')

            cols.pop(ix_timestamp)
            cols.pop(ix_metric_value - 1)
            for row in data['tables'][0]['rows']:
                timestamp = row.pop(ix_timestamp)
                metric_value = row.pop(ix_metric_value - 1)
                sfx_values.append({
                        'metric': query_data.get('metric_name'),
                        'value': metric_value,
                        'timestamp': parse(timestamp).timestamp() * 1000,
                        'dimensions': {**dict(zip(cols, row)), **extra_dimensions}
                    })
            sfx.send(**{f"{query_data.get('metric_type')}s": sfx_values})


if __name__ == "__main__":
    run()
