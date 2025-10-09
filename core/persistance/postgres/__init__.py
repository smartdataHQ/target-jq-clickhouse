import logging
import os

import dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

dotenv.load_dotenv()
logger = logging.getLogger(__name__)

ENVIRONMENT = os.getenv("ENVIRONMENT")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", 5432)

DATABASE_URL = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

connection = None
engine = None
async_engine = None
async_session = None
try:
    # connection = psycopg2.connect(database=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST, port=POSTGRES_PORT, sslmode='require') if POSTGRES_HOST else None
    if ENVIRONMENT not in ["onprem"] and POSTGRES_HOST:
        async_engine = create_async_engine(DATABASE_URL, echo=True)
        # engine = create_engine(DATABASE_URL, echo=True)
        # async_session = sessionmaker(connection, class_=AsyncSession, expire_on_commit=False)
        print(f"Connected to Postgres: {POSTGRES_HOST}")
except Exception as e:
    connection = None
    logger.error(f"Error connecting to Postgres: {str(e)}")
    # fail silently


def async_session_generator():
    if ENVIRONMENT in ["onprem"]:
        return None
    return sessionmaker(engine, class_=AsyncSession)
