import uuid

from cxs.core.authentication.utils import ServiceToken
from cxs.core.schema.services import *
from cxs.core.schema.solutions import *


class ReassignmentConfig(CXSSchema):
    name: str = Field(description="", default=None)
    target: str = Field(description="", default=None)
    reg_extract: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)


class PersistConfig(CXSSchema):
    table: str = Field(description="", default="cst.semantic_events")
    reassign: Annotated[Optional[list[ReassignmentConfig]], OmitIfNone()] = Field(
        description="", default=None
    )
    overwrite: Annotated[Optional[dict[str, str]], OmitIfNone()] = Field(
        description="", default=None
    )
    ignore: Annotated[Optional[list[str]], OmitIfNone()] = Field(description="", default=None)


class AccountConfig(CXSSchema):
    name: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)
    id: uuid.UUID = Field(description="", default=None)
    organization_gid: uuid.UUID = Field(description="", default=None)
    partitions: list[str] = Field(..., description="")
    default_language: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)


class CredentialsConfig(CXSSchema):
    type: str = Field(..., description="")
    id: str = Field(..., description="")
    email: Annotated[Optional[str], OmitIfNone()] = Field(description="", default=None)


class ComponentConfig(CXSSchema):

    id: uuid.UUID = Field(description="", default=None)

    account: Annotated[Optional[AccountConfig], OmitIfNone()] = Field(description="", default=None)
    credentials: Annotated[Optional[CredentialsConfig], OmitIfNone()] = Field(description="", default=None)

    service: Annotated[Optional[Service], OmitIfNone()] = Field(description="", default=None)
    component: Annotated[Optional[Component], OmitIfNone()] = Field(description="", default=None)
    config: Annotated[Optional[dict[str, Any]], OmitIfNone()] = Field(description="", default=None)

    solutions: Annotated[Optional[list[Solution]], OmitIfNone()] = Field(description="", default=None)
    prompts: Annotated[Optional[list[CustomPrompt]], OmitIfNone()] = Field(description="", default=None)
    scripts: Annotated[Optional[list[CustomScript]], OmitIfNone()] = Field(description="", default=None)
    datasets: Annotated[Optional[list[CustomDataset]], OmitIfNone()] = Field(description="", default=None)
    documents: Annotated[Optional[list[DocumentService]], OmitIfNone()] = Field(description="", default=None)

    persist: Annotated[Optional[list[PersistConfig]], OmitIfNone()] = Field(description="", default=None)
    logging: Annotated[Optional[list[PersistConfig]], OmitIfNone()] = Field(description="", default=None)


class APIServiceConfig(CXSSchema):
    account: Annotated[Optional[AccountConfig], OmitIfNone()] = Field(description="", default=None)
    service: Annotated[Optional[Service], OmitIfNone()] = Field(..., description="")
    component: Annotated[Optional[ComponentConfig], OmitIfNone()] = Field(description="", default=None)
    solutions: Annotated[Optional[list[LinkedSolution]], OmitIfNone()] = Field(description="", default=None)
    token: Annotated[Optional[ServiceToken], OmitIfNone()] = Field(description="", default=None)

