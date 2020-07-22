import logging

from report_backups.app import main as report


class Timer:
    def __init__(self):
        pass

    def past_due(self):
        pass


if __name__ == '__main__':
    logger = logging.getLogger('report_backups')
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    logger.setLevel(logging.DEBUG)
    report(Timer)
