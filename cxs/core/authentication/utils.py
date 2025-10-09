import logging
import os
from datetime import UTC, datetime, timedelta, timezone
from typing import Annotated

import dotenv
import jwt
from aiocache import cached
from aiocache.serializers import PickleSerializer
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from cxs.core.persistance.postgres import async_engine
from cxs.core.schema.model.alchemy import Account, ApiKey, WriteKey

dotenv.load_dotenv()
logger = logging.getLogger(__name__)

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ENVIRONMENT = os.getenv("ENVIRONMENT")
# set default to 1 hour
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    client_id: str | None = None
    partitions: list[str] | None = None
    exp: int | None = None


class AuthorizedUser(BaseModel):
    username: str | None = None
    email: str | None = None
    name: str | None = None

    api_key_id: str | None = None
    client_id: str | None = None
    account_gid: str | None = None
    partitions: list[str] | None = None

    hashed_password: str | None = None
    active: bool | None = None
    active_until: datetime | None = None


class ServiceToken(BaseModel):
    account_id: str | None = None
    client_ip: str | None = None

    organization: str | None = None
    organization_gid: str | None = None
    write_key: str | None = None
    partitions: list[str] | None = None

    active: bool | None = None
    active_until: datetime | None = None

    services: list[str] | None = None
    components: list[str] | None = None
    apis: list[str] | None = None


class UserInDB(AuthorizedUser):
    hashed_password: str


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


@cached(ttl=120, serializer=PickleSerializer())
async def get_write_key(
    write_key: str,
    organization_gid: str,
    host_ip: str,
    apis: list[str] = None,
    services: list[str] = None,
    components: list[str] = None,
) -> ServiceToken | None:

    async with AsyncSession(async_engine) as session:
        results = await session.execute(
            select(WriteKey)
            .where(WriteKey.key == write_key)
            .join(Account, Account.organization_gid == organization_gid)
            .options(contains_eager(WriteKey.account))
        )
        write_key = results.scalars().first()
        # 'cQW2!E3el8k4o3tt' - 'd7914036-e6e5-44ee-9626-900dc75807b0' // 9a5eae2e-4533-5452-b618-6f3bc7c46629

    if not write_key:
        return None

    return ServiceToken(
        **{
            "write_key": write_key.key,
            "organization": write_key.account.name,
            "organization_gid": str(write_key.account.organization_gid),
            "account_id": str(write_key.account_id),
            "partitions": list(
                set(
                    (write_key.partition).split(",")
                    if write_key.partition
                    else write_key.account.partition.split(",")
                )
            ),
            "active": write_key.enabled
            and write_key.account.active
            and (write_key.active_until is None or write_key.active_until > datetime.now()),
            "active_until": write_key.active_until,
            "client_ip": host_ip,
            "apis": apis if apis else ["documents", "entities", "products", "llm", "vectors", "components"],
            "services": services if services else [],
            "components": components if components else [],
        }
    )


@cached(ttl=120, serializer=PickleSerializer())
async def get_user_with_api_key(client_id, client_secret=None, scopes=None, grant_type=None):

    async with AsyncSession(async_engine) as session:
        results = await session.execute(
            select(ApiKey)
            .where(ApiKey.client_id == client_id)
            .join(ApiKey.account)
            .join(ApiKey.user, isouter=True)
            .options(contains_eager(ApiKey.account), contains_eager(ApiKey.user))
        )
        api_key = results.scalars().first()

    if not api_key:
        return None

    return AuthorizedUser(
        **{
            "username": api_key.user.email if api_key.user else "",
            "email": api_key.user.email if api_key.user else "",
            "name": api_key.name,
            "client_id": str(api_key.client_id),
            "api_key_id": str(api_key.id),
            "hashed_password": api_key.client_secret,
            "partitions": api_key.account.partition.split(","),
            "active": api_key.active and api_key.account.active,
        }
    )


async def authenticate_user(
    username: str,
    password: str,
    client_id: str,
    client_secret: str,
    scopes: str,
    grant_type: str,
):

    user = None
    if client_id and client_secret:
        user = await get_user_with_api_key(client_id, client_secret, scopes, grant_type)

    if not user:
        return False

    if client_id and client_secret:
        if not verify_password(plain_password=client_secret, hashed_password=user.hashed_password):
            return False
    else:
        if not verify_password(plain_password=password, hashed_password=user.hashed_password):
            return False

    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not payload.get("client_id") or not payload.get("partitions"):
            raise credentials_exception

        token_data = TokenData(**payload)
    except InvalidTokenError:
        raise credentials_exception

    try:
        user = await get_user_with_api_key(client_id=token_data.client_id)
    except Exception:
        raise credentials_exception

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(current_user: Annotated[AuthorizedUser, Depends(get_current_user)]):
    if not current_user.active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return current_user


def validate_partitions(
    service_token: ServiceToken,
    requested_partitions: list[str] | None = None,
) -> list[str]:
    if not requested_partitions:
        return service_token.partitions

    if requested_partitions:
        if not set(requested_partitions).issubset(set(service_token.partitions)):
            raise HTTPException(403, "Partition not authorized")
        return requested_partitions

    return service_token.partitions


def get_valid_service_token(request: Request, service_type: str) -> ServiceToken:
    try:
        client_ip = request.client.host
        service_token = ServiceToken(**assert_token(request))

        if service_type != "inspect":
            if (
                ENVIRONMENT not in ["onprem"]
                and service_token.client_ip
                and service_token.client_ip != client_ip
            ):
                logger.debug("Token rejected: %s != %s", service_token.client_ip, client_ip)
                raise HTTPException(403, "Unusable Service Token")

            if service_token.active_until:
                # timestamps are tricky, and sometimes have tz info, sometimes not. this attempts
                # to handle both cases
                if service_token.active_until.tzinfo is None:
                    active_until_utc = service_token.active_until.replace(tzinfo=timezone.utc)
                else:
                    active_until_utc = service_token.active_until.astimezone(timezone.utc)

                if active_until_utc < datetime.now(UTC):
                    logger.debug("Token expired")
                    raise HTTPException(403, "Expired Service Token")

            if not service_token.active:
                logger.debug("Token is not active")
                raise HTTPException(403, "Expired Service Token")

            if (
                service_token.services
                and len(service_token.services) > 0
                and service_type not in service_token.services
            ):
                raise HTTPException(403, "Unauthorized Service")

        return service_token
    except InvalidTokenError as e:
        logger.debug("Error decoding token: %s", str(e))
        raise HTTPException(403, "Invalid Service Token")


def assert_token(request: Request) -> dict:
    token = request.headers.get("authorization")
    if not token:
        logger.debug("No token, check 'authorization' header")
        raise HTTPException(403, "Invalid Service Token")
    try:
        return jwt.decode(token.split(" ")[-1], SECRET_KEY, algorithms=[ALGORITHM])
    except InvalidTokenError as e:
        logger.debug("Error decoding token: %s", str(e))
        raise HTTPException(403, "Invalid Service Token")


def assert_service_access(token: dict, service_type: str) -> ServiceToken:
    try:
        service_token = ServiceToken(**token)
        if service_type not in service_token.apis:
            raise HTTPException(403, "Unauthorized Service")

        return service_token
    except InvalidTokenError as e:
        logger.debug("Error decoding token: %s", str(e))
        raise HTTPException(403, "Invalid Service Token")
