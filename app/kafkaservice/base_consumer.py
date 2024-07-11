"""Base consumer of Kafka topic"""

import json
import logging
import sys
import threading
from abc import abstractmethod
from typing import Dict
from datetime import datetime

from confluent_kafka import Consumer, Producer
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from common.exceptions import (
    BootstrapServersKafkaException,
    CreateConsumerKafkaException,
    GroupIdKafkaException,
    SubscribeKafkaTopicException,
    TopicKafkaException,
)
from settings.settings import settings

logger = logging.getLogger(__name__)


def get_default_config() -> Dict[str, str]:
    """Default config for kafka."""

    default_config = {
        "auto.offset.reset": "earliest",
        "heartbeat.interval.ms": 1000,
        "enable.auto.commit": False,
    }

    config = {
        "bootstrap.servers": settings.KAFKA_BINDER_BROKERS,
        "group.id": settings.CONSUMER_GROUP_NAME,
        "security.protocol": "PLAINTEXT",
    }

    default_config.update(config)
    return default_config


class ManagedProducer:
    def __init__(self):
        self.config = config = {
            "bootstrap.servers": settings.KAFKA_BINDER_BROKERS,
        }
        self.producer = Producer(self.config)

    def __enter__(self):
        return self.producer

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.producer.flush()


class BaseConsumer:
    """Base class of Kafka Consumer."""

    def __init__(
        self,
        topics: str,
        consumer_name: str = __name__,
        thread_id: str = "",
    ) -> None:
        self.config = get_default_config()
        self.topics = topics
        self.consumer_name = consumer_name
        self.thread_id = thread_id
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_HOST,
            aws_access_key_id=settings.S3_USERNAME,
            aws_secret_access_key=settings.S3_PASSWORD,
            config=Config(signature_version="s3v4"),
        )

        if (
            "bootstrap.servers" not in self.config
            or not self.config["bootstrap.servers"]
        ):
            raise BootstrapServersKafkaException(
                "Kafka bootstrap.servers not specified."
            )
        if not self.config["group.id"]:
            raise GroupIdKafkaException("Kafka group.id group not specified.")
        if not topics:
            raise TopicKafkaException("Kafka topics not specified.")

        try:
            self.consumer = Consumer(self.config)
        except Exception as err:
            logger.exception(f"Cannot create consumer {consumer_name}: {err}")
            error_detail = f"Exception -- Cannot create consumer {consumer_name}"
            raise CreateConsumerKafkaException(error_detail) from err

        try:
            self.consumer.subscribe([topics])
        except Exception as err:
            logger.exception(f"Cannot subscribe to topics {topics}: {err}")
            error_detail = (
                f"Exception -- CONSUMER {consumer_name}" f" cannot subscribe to topics"
            )
            raise SubscribeKafkaTopicException(error_detail) from err

    def send_failed_msg_to_dlq(self, topic: str, message: dict):
        """send to dlq if encouring any error"""
        try:
            with ManagedProducer() as producer:
                payload = json.dumps(message).encode("utf-8")
                producer.produce(topic, payload)
        except Exception as e:
            print(f"Failed to send message to Kafka: {e}")

    def create_bucket_if_not_exists(self, bucket_name):
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            print(f"Bucket '{bucket_name}' already existed.")
        except ClientError:
            self.s3_client.create_bucket(Bucket=bucket_name)
            print(f"Bucket '{bucket_name}' was created successfully.")

    def store_s3_json(self, items: list, bucket_name: str):
        try:
            current_date = datetime.now().strftime("%Y/%m/%d")
            prefix = f"{settings.S3_BASE_PREFIX}/{current_date}/type=json"
            file_name = f"{prefix}/users_{datetime.now().strftime('%H%M%S')}.json"
            self.create_bucket_if_not_exists(bucket_name)
            json_data = json.dumps(items)
            self.s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=json_data)
        except Exception as e:
            print(f"Error: {e}")

    def store_s3_parquet(self, items: list, bucket_name: str):
        try:
            current_date = datetime.now().strftime("%Y/%m/%d")
            prefix = f"{settings.S3_BASE_PREFIX}/{current_date}/type=parquet"
            file_name = f"{prefix}/users_{datetime.now().strftime('%H%M%S')}.parquet"
            self.create_bucket_if_not_exists(bucket_name)
            df = pd.DataFrame(items)
            table = pa.Table.from_pandas(df)
            pq.write_table(table, "temp.parquet")
            with open("temp.parquet", "rb") as data:
                self.s3_client.put_object(Body=data, Bucket=bucket_name, Key=file_name)
        except Exception as e:
            print(f"Error: {e}")

    @abstractmethod
    def process_msg(self, msg: str) -> None:
        """Process message for Consumer."""

    def run(self) -> None:
        """Get message from kafka topic and process it."""
        current_thread = threading.current_thread()
        logger.info(f"Start thread {current_thread} to handle {self.consumer_name}")
        try:
            while getattr(current_thread, "keep_running", True):
                try:
                    msgs = self.consumer.consume(
                        num_messages=int(settings.MAX_MESSAGES),
                        timeout=int(settings.CONSUMER_TIMEOUT),
                    )
                    if not msgs:
                        continue

                    try:
                        self.process_msg(msgs)
                    except Exception as exc:
                        error_detail = f"Consumer {self.consumer_name} Escalate exception {exc} due to message consumption error."
                        logger.exception(error_detail)
                        print(error_detail)
                        continue
                    else:
                        try:
                            self.consumer.commit(asynchronous=False)
                        except Exception as exc:
                            error_detail = f"CONSUMER {self.consumer_name} Escalate exception {exc} due to SYNC commit error."
                            logger.exception(error_detail)
                            print(error_detail)
                            continue
                except KeyboardInterrupt:
                    break
        finally:
            logger.info(f"Close thread {current_thread} consumer {self.consumer_name}")
            self.consumer.close()
            sys.exit()
