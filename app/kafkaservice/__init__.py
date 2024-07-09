"""Init file of Kafka."""

import logging

from app.kafkaservice.mysql_users_kafka_consumer import (
    create_mysql_users_event_kafka_consumer,
)

logger = logging.getLogger(__name__)
CONSUMER_KAFKA_THREAD_LIST = []


def start_pull_data_from_kafka() -> None:
    """Start Multi Threading to handle pull data for Kafka."""
    for thread in [
        create_mysql_users_event_kafka_consumer(),
    ]:
        logger.info(f"Starting thread {thread.name}")
        thread.start()
        logger.info(f"Started thread {thread.name}")
        CONSUMER_KAFKA_THREAD_LIST.append(thread.name)
