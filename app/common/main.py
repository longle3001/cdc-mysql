import logging
import os
import sys

from pythonjsonlogger import jsonlogger

current_directory = os.getcwd().replace("common", "")
sys.path.insert(0, current_directory)
current_directory = current_directory + "/app"
sys.path.insert(0, current_directory)
from kafkaservice import start_pull_data_from_kafka
from settings.settings import settings

FORMAT = "%(levelname)s: {%(filename)s:%(lineno)d} - %(message)s"


def setup_logging():
    """Setup logging for the application."""
    logger = logging.getLogger()
    environment = settings.ENVIRONMENT
    formatter = CustomJsonFormatter(FORMAT)
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(formatter)
    if environment in ["prd", "stg", "local"]:
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG
    logger.setLevel(log_level)
    logger.addHandler(log_handler)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custome Json formatter."""

    def add_fields(self, log_record, record, message_dict):
        """Add more logic to handle format logging."""

        super().add_fields(log_record, record, message_dict)

        if log_record.get("level"):
            log_record["level"] = log_record["level"].upper()
        else:
            log_record["level"] = record.levelname


def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    start_pull_data_from_kafka()
    logger.info("starting service")


if __name__ == "__main__":
    main()
