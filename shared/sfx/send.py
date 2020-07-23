import logging
from typing import List

import signalfx

logger = logging.getLogger('shared.sfx.send')


def send_status_to_sfx(org_token: str,
                       sfx_realm: str = 'eu0',
                       gauges: List[dict] = None,
                       counters: List[dict] = None,
                       cumulative_counters: List[dict] = None) -> bool:
    """
    Send backup status to SFX. If a VM is not found in the Backup Vault
    the backup for this VM is considered as failed with vault_name to Unknown.
    :param org_token: SignalFx Organisation token
    :type org_token: str
    :param sfx_realm: SignalFx realm. Default to eu0
    :type sfx_realm: str
    :param gauges: List of gauges metrics to send to SignalFx
    :type gauges: List[dict]
    :param counters: List of counters metrics to send to SignalFx
    :type counters: List[dict]
    :param cumulative_counters: List of cumulative counters metrics to send to SignalFx
    :type cumulative_counters: List[dict]
    :return: Boolean
    :rtype: bool
    """

    sfx = signalfx.SignalFx(api_endpoint=f'https://api.{sfx_realm}.signalfx.com',
                            ingest_endpoint=f'https://ingest.{sfx_realm}.signalfx.com',
                            stream_endpoint=f'https://stream.{sfx_realm}.signalfx.com'
                            )

    ingest = sfx.ingest(org_token)

    # TODO: Add resource_tags as dimention

    try:
        logger.info("Send data to SignalFX")
        ingest.send(
            gauges=gauges,
            counters=counters,
            cumulative_counters=cumulative_counters
        )
        return True
    except Exception as e:
        logger.error('Failed to send metrics to SignalFx')
        logger.debug('SignalFx Error message: %s', e)
        return False
    finally:
        ingest.stop()
