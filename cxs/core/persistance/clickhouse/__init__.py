import logging
import os

import dotenv
from clickhouse_connect import get_async_client
from clickhouse_connect import get_client

dotenv.load_dotenv()
logger = logging.getLogger(__name__)

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD")

ch_async_client = None
try:
    ch_async_client = (
        get_async_client(
            host=CLICKHOUSE_HOST,
            username=CLICKHOUSE_USER,
            password=CLICKHOUSE_PASSWORD,
            settings={
                "async_insert": 1,
                "wait_for_async_insert": 0,
                "async_insert_busy_timeout_ms": 5000,
                "async_insert_max_data_size": 100_000_000,
                "async_insert_max_query_number": 450_000,
            },
        )
        if CLICKHOUSE_HOST
        else None
    )
    if ch_async_client is not None:
        print(f"Connected to Clickhouse (async): {CLICKHOUSE_HOST}")
except Exception as e:
    ch_async_client = None
    logger.error(f"Error connecting to ClickHouse: {str(e)}")
    # fail silently

ch_client = None
try:
    ch_client = (
        get_client(
            host=CLICKHOUSE_HOST,
            username=CLICKHOUSE_USER,
            password=CLICKHOUSE_PASSWORD,
        )
        if CLICKHOUSE_HOST
        else None
    )
    if ch_client is not None:
        print(f"Connected to Clickhouse (sync): {CLICKHOUSE_HOST}")
except Exception as e:
    ch_client = None
    logger.error(f"Error connecting to ClickHouse: {str(e)}")
    # fail silently

ch_streaming_client = None
try:
    ch_streaming_client = (
        get_client(host=CLICKHOUSE_HOST, username=CLICKHOUSE_USER, password=CLICKHOUSE_PASSWORD)
        if CLICKHOUSE_HOST
        else None
    )
    if ch_streaming_client is not None:
        print(f"Connected to Clickhouse (streaming): {CLICKHOUSE_HOST}")
except Exception as e:
    ch_streaming_client = None
    logger.error(f"Error connecting to ClickHouse: {str(e)}")
    # fail silently
