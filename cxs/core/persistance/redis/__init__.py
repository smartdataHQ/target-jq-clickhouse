import logging
import os
import dotenv
import redis

dotenv.load_dotenv()
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_USER = os.getenv("REDIS_USER")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_DB = os.getenv("REDIS_DB")


connection = None
try:
    # if we have user+pass OR host then we try to connect
    if (REDIS_USER and REDIS_PASSWORD) or REDIS_HOST:
        if REDIS_USER or REDIS_PASSWORD:
            if "," in REDIS_HOST:
                connection = redis.RedisCluster(
                    host=REDIS_HOST.split(",")[0],
                    port=6379,
                    decode_responses=True,
                    username=REDIS_USER,
                    password=REDIS_PASSWORD,
                )
            else:
                connection = redis.Redis(
                    host=REDIS_HOST,
                    port=6379,
                    decode_responses=True,
                    db=REDIS_DB,
                    username=REDIS_USER,
                    password=REDIS_PASSWORD,
                )
        else:
            if "," in REDIS_HOST:
                connection = redis.RedisCluster(
                    host=REDIS_HOST.split(",")[0],
                    port=6379,
                    decode_responses=True,
                )
            else:
                connection = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True, db=REDIS_DB)
        print(f"Connected to Redis: {connection}")
except Exception as e:
    connection = None
    logger.error(f"Error connecting to Redis: {str(e)}")
