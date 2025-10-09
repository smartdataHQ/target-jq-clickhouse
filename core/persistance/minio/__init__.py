import logging
import os
from typing import TYPE_CHECKING, AsyncContextManager

import aioboto3
from aioboto3.session import Session

if TYPE_CHECKING:
    from types_aiobotocore_s3.client import S3Client

logger: logging.Logger = logging.getLogger(__name__)

MINIO_ENDPOINT: str | None = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY: str | None = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY: str | None = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET_NAME: str = os.getenv("MINIO_BUCKET_NAME", "job-files")
MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT")

# Global session for creating clients
minio_session: Session | None = None
minio_config: dict[str, str] | None = None

try:
    if MINIO_ENDPOINT and MINIO_ACCESS_KEY and MINIO_SECRET_KEY and ENVIRONMENT not in ["onprem"]:
        minio_session = aioboto3.Session()
        minio_config = {
            "endpoint_url": f"{'https' if MINIO_SECURE else 'http'}://{MINIO_ENDPOINT}",
            "aws_access_key_id": MINIO_ACCESS_KEY,
            "aws_secret_access_key": MINIO_SECRET_KEY,
        }
        print(f"Connected to MinIO: {MINIO_ENDPOINT}")
    else:
        minio_session = None
        minio_config = None
        logger.warning("MinIO configuration incomplete - session not initialized")
except Exception as e:
    minio_session = None
    minio_config = None
    logger.error("Error initializing MinIO session: %s", e, exc_info=e)


def get_minio_client() -> AsyncContextManager["S3Client"]:
    """
    Get a MinIO S3 client context manager

    Usage:
        async with get_minio_client() as s3:
            await s3.put_object(...)

    Returns:
        Async context manager for S3Client

    Raises:
        RuntimeError: If MinIO session not initialized
    """
    if minio_session is None or minio_config is None:
        raise RuntimeError("MinIO session not initialized. Check your environment variables.")

    return minio_session.client("s3", **minio_config)  # type: ignore


def is_minio_available() -> bool:
    """Check if MinIO is available and configured"""
    return minio_session is not None and minio_config is not None
