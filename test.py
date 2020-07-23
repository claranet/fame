import logging

from report_backups.app import main as report


class Timer:
    def __init__(self):
        pass

    def past_due(self):
        pass


if __name__ == '__main__':
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    sfx_logger = logging.getLogger('signalfx.ingest')
    sfx_logger.setLevel(logging.INFO)

    urllib_logger = logging.getLogger('urllib3')
    urllib_logger.setLevel(logging.INFO)

    azure_logger = logging.getLogger('azure')
    azure_logger.setLevel(logging.INFO)

    msrest_logger = logging.getLogger('msrest')
    msrest_logger.setLevel(logging.INFO)

    report(Timer)
