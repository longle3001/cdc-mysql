import json
import logging
import threading
import uuid
from datetime import datetime

from confluent_kafka import KafkaError, KafkaException

from common.common import MYSQL_DB_USERS_TOPIC, MYSQL_DB_USERS_TOPIC, MYSQL_DB_USERS_DLQ_TOPIC
from common.schema import user_schema
from kafkaservice.base_consumer import BaseConsumer


logger = logging.getLogger(__name__)


class MysqlEventConsumer(BaseConsumer):
    """The Consumer of Topic mongo users"""

    def _create_new_record(self, is_deleted:bool=False, message:dict={}):
        temp = user_schema.copy()
        if "id" not in message.keys() or not message["id"]:
            return
        temp["id"] = message["id"]
        temp["name"] = message["name"] if "name" in message.keys() else ""
        temp["email"] = message["email"] if "email" in message.keys() else ""
        temp["last_update"] = str(datetime.now())
        if is_deleted:
            temp["is_deleted"]=1
        return temp


    def process_create_update(self, messages: list):
        logger.info("-----process_create_update-----")
        # for message in messages:
        users = []
        for message in messages:
            try:
                if message["op"] in ["c","u"]:
                    message = message["after"]
                    temp = self._create_new_record(is_deleted=False,message=message)
                else:
                    message = message["before"]
                    temp = self._create_new_record(is_deleted=True,message=message)
                users.append(temp)
            except Exception as e:
                message["error_message"] = f"Error processing data: {str(e)}"
                logger.error(f"FAIL: {str(e)} with the full message {message}")
                self.send_failed_msg_to_dlq(MYSQL_DB_USERS_DLQ_TOPIC, message)

        self.store_s3_json(items=users, bucket_name="bucket-user-test")
        self.store_s3_parquet(items=users, bucket_name="bucket-user-test")
        return users


    def process_msg(self, msgs: str) -> str:
        """Process message for mysql users kafka Consumer.

        Get Data from Kafka Topic.
        Send it to s3.
        """
        try:
            if msgs is None:
                return
            batch_messages = []
            set_partition = set()
            for msg in msgs:
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        continue
                    elif msg.error():
                        raise KafkaException(msg.error())
                elif msg.value():
                    set_partition.add(msg.partition())
                    message = json.loads(msg.value().decode("utf-8"))
                    message = message["payload"]
                    batch_messages.append(message)
            if batch_messages:
                self.process_create_update(batch_messages)
                    

        except Exception as exc:
            logger.exception(
                "Cannot convert message from string to dictionary: %s", exc
            )


def create_mysql_users_event_kafka_consumer() -> threading.Thread:
    """Create threading to handle process of mysql users event consumer."""
    thread_id = str(uuid.uuid4())

    kafka_input = {
        "topics": MYSQL_DB_USERS_TOPIC,
        "consumer_name": "mysql_db_users_kafka_consumer",
        "thread_id": thread_id,
    }
    mysql_users_event_consumer = MysqlEventConsumer(**kafka_input)
    logger.info("mysql Users Event Kafka Consumer.")

    mysql_users_event_consumer_thread = threading.Thread(
        target=mysql_users_event_consumer.run,
        name=f"mysql-users-event-kafka-consumer-{thread_id}",
    )
    return mysql_users_event_consumer_thread
