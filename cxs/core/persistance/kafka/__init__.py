import json
import logging
import os

import dotenv
from kafka import KafkaProducer

dotenv.load_dotenv()
logger = logging.getLogger(__name__)

KAFKA_HOSTS = os.getenv("KAFKA_HOSTS")
KAFKA_USER = os.getenv("KAFKA_USER")
KAFKA_PASSWORD = os.getenv("KAFKA_PASSWORD")
ENVIRONMENT = os.getenv("ENVIRONMENT")

producer = None

try:
    if KAFKA_HOSTS and ENVIRONMENT not in ["onprem"]:

        producer = KafkaProducer(
            bootstrap_servers=KAFKA_HOSTS,
            security_protocol="SASL_PLAINTEXT",
            sasl_mechanism="PLAIN",
            sasl_plain_username=KAFKA_USER,
            sasl_plain_password=KAFKA_PASSWORD,
            value_serializer=lambda x: json.dumps(x).encode("utf-8"),
            key_serializer=lambda x: x.encode("utf-8") if x else None,
            linger_ms=10,
            batch_size=65_535,
            request_timeout_ms=10_000,
            retries=3,
            retry_backoff_ms=500,
        )
except Exception as e:
    producer = None
    logger.error("Error connecting to Kafka: %s", e, exc_info=e)
