from datetime import datetime
from enum import Enum
from typing import Annotated
from typing import Any
from typing import Optional

import pydantic
from pydantic import Field
from pydantic import Json
from cxs.core.schema import CXSSchema
from cxs.core.schema.search_document import OmitIfNone


class ServiceType(CXSSchema):
    some: str = Field(..., description="")


class Service(CXSSchema):
    id: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    name: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    slug: Annotated[Optional[str], OmitIfNone()] = Field( description="", default=None)


class ServiceAccess(CXSSchema):
    some: str = Field(..., description="")


class Component(CXSSchema):
    id: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    name: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    slug: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)

    component_group: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    component_type: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    component_variant: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)

    icon: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    public: Annotated[Optional[bool], OmitIfNone()] = Field(description="", default=None)
    can_be_modified: Annotated[Optional[bool], OmitIfNone()] = Field(description="", default=None)
    description: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    documentation: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    documentation_url: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    core_settings: Annotated[Optional[Json], OmitIfNone()] = Field(description="", default=None)
    current_version: Annotated[Optional[float], OmitIfNone()] = Field(description="", default=None)
    date_created: Annotated[Optional[datetime], OmitIfNone()] = Field(description="", default=None)
    active_from: Annotated[Optional[datetime], OmitIfNone()] = Field(description="", default=None)
    active_until: Annotated[Optional[datetime], OmitIfNone()] = Field(description="", default=None)


class InitiatedComponent(Component):
    handler: Any = Field(description="", default=None)


class ServiceComponent(CXSSchema):
    some: str = Field(..., description="")


class PromptRole(Enum):
    system = "system"
    user = "user"


class CustomPrompt(CXSSchema):
    sequence: Annotated[Optional[int], OmitIfNone()] = Field(
        description="The order of the prompt in a list of prompts", default=None
    )
    role: Annotated[Optional[PromptRole], OmitIfNone()] = Field(
        description="The role speaking as recognized by the LLM processing the prompt", default=None
    )
    content: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The content as raw text or as a template", default=None
    )
    processed_content: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The content after template rendering", default=None
    )
    settings: Annotated[Optional[Json], OmitIfNone()] = Field(
        description="Additional settings for the prompt. it's used for template rendering as well as other variables",
        default=None,
    )


class LinkedPrompt(CXSSchema):
    role: str = Field(..., description="")
    content: str = Field(..., description="")
    sequence: int = Field(..., description="")


class ServiceComponentPrompt(CXSSchema):
    some: str = Field(..., description="")


class CustomDataset(CXSSchema):
    name: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    type: Annotated[Optional[str], OmitIfNone()] = Field(
        description="", default=None
    )  # local, sql, graphql
    variant: Annotated[Optional[str], OmitIfNone()] = Field(
        description="", default=None
    )  # json, csv etc.
    json_schema: Annotated[Optional[list[dict]], OmitIfNone()] = Field(
        description="", default=None
    )  # described as json schema
    data: Annotated[Optional[list[dict | Any]], OmitIfNone()] = Field(
        description="", default=None
    )  # data in the dataset


class LinkedDataset(CXSSchema):
    some: str = Field(..., description="")


class ServiceComponentDataset(CXSSchema):
    some: str = Field(..., description="")


class CustomScript(CXSSchema):
    script: Annotated[str, OmitIfNone()] = Field(description="", default=None)
    processed_script: Annotated[str, OmitIfNone()] = Field(description="", default=None)
    some: str = Field(..., description="")


class LinkedScript(CXSSchema):
    some: str = Field(..., description="")


class ServiceComponentScript(CXSSchema):
    some: str = Field(..., description="")


class DocumentService(CXSSchema):
    some: str = Field(..., description="")


class ServiceComponentDocument(CXSSchema):
    some: str = Field(..., description="")


class ServiceComponentLink(CXSSchema):
    some: str = Field(..., description="")
