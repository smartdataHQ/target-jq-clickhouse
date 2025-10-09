from pydantic import Field
from cxs.core.schema import CXSSchema


class ConfigAccountUser(CXSSchema):
    some: str = Field(..., description="")


class Account(CXSSchema):
    name: str = Field(..., description="")
    organization_gid: str = Field(..., description="")
    partitions: list[str] = Field(..., description="")


class User(CXSSchema):
    some: str = Field(..., description="")


class Credentials(CXSSchema):
    some: str = Field(..., description="")


class ApiKey(Credentials):
    some: str = Field(..., description="")


class WriteKey(Credentials):
    some: str = Field(..., description="")
