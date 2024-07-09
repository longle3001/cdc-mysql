"""This file to use read config from enviroment."""

import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    KAFKA_BINDER_BROKERS: str = os.getenv(
        "KAFKA_BINDER_BROKERS",
        "localhost:29092",  # need to change localhost --> kafka
    )
    CONSUMER_GROUP_NAME: str = os.getenv(
        # "KAFKA_CONSUMER_GROUP", "data-warehouse-streaming-group"
        "KAFKA_CONSUMER_GROUP",
        "my-group-1",
    )
    CONSUMER_TIMEOUT: str = os.getenv("CONSUMER_TIMEOUT", "5")
    MAX_MESSAGES: str = os.getenv("MAX_MESSAGES", "200")
    ENVIRONMENT: str = os.getenv("Environment", "local")
    REQUEST_TIMEOUT: str = os.getenv("REQUEST_TIMEOUT", "5")
    S3_HOST: str = os.getenv("S3_HOST", "http://localhost:9000")
    S3_USERNAME: str = os.getenv("S3_USERNAME", "minio")
    S3_PASSWORD: str = os.getenv("S3_PASSWORD", "minio123")
    S3_BASE_PREFIX: str = os.getenv("S3_BASE_PREFIX", "test")
    

    class Config:
        case_sensitive = True


settings = Settings()
