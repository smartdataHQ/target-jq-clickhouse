from datetime import datetime
from typing import Annotated, List, Any, Optional
from pydantic import Field
from pydantic import Json
from cxs.core.schema import CXSSchema, OmitIfNone, empty_list


class Solution(CXSSchema):
    name: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    type: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    provider: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    variant: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    label: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    connect_url: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    slug: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    settings: Annotated[Optional[dict[str, Any]], OmitIfNone()] = Field(description="", default=None)

class LinkedSolution(CXSSchema):
    name: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    type: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)

    provider: Annotated[Optional[str], OmitIfNone()] = Field(description="Provider of the solution", default=None)
    solution: Annotated[Optional[str], OmitIfNone()] = Field(description="The solution", default=None)
    variant: Annotated[Optional[str], OmitIfNone()] = Field(description="Slug of the variant", default=None)

    account: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    username: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    password: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    api_key: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    connect_url: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    partition: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)

    settings: Annotated[Optional[dict[str, Any]], OmitIfNone()] = Field(description="", default=None)
    supported_actions: Annotated[Optional[list[str]], OmitIfNone()] = Field(description="", default_factory=lambda: empty_list())

class InitiatedSolution(LinkedSolution):
    handler: Any = Field(description="", default=None)


class SolutionVariant(CXSSchema):
    name: str = Field(..., description="")
    slug: str = Field(..., description="")


class SolutionPricing(CXSSchema):
    some: str = Field(..., description="")


class SolutionLink(CXSSchema):
    solution: Solution = Field(..., description="")

    account_name: str = Field(..., description="")
    username: str = Field(..., description="")
    connect_url: str = Field(..., description="")

    password: str = Field(..., description="")
    api_key: str = Field(..., description="")
    certificate: str = Field(..., description="")
    headers: Json = Field(..., description="")

    settings: Json = Field(..., description="")
    custom_pricing: Json = Field(..., description="")

    occurs_cost: bool = Field(..., description="")
    log_usage: bool = Field(..., description="")
    active: bool = Field(..., description="")
    archived: bool = Field(..., description="")
    reusable: bool = Field(..., description="")

    date_created: datetime = Field(..., description="")
    active_from: datetime = Field(..., description="")
    active_until: datetime = Field(..., description="")
