from datetime import datetime
from typing import List
from typing import Optional
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy_json import mutable_json_type

from . import CXSBaseModel

account_routers: [APIRouter] = []
account_routers_hidden: [APIRouter] = []


class AccountUser(CXSBaseModel):
    __tablename__ = "account_users"

    key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    permission: Mapped[Optional[str]]
    onboarded: Mapped[Optional[bool]]

    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"), primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("account.id"), primary_key=True)

    user: Mapped["User"] = relationship(back_populates="user_accounts")
    account: Mapped["Account"] = relationship(back_populates="account_users")


class Account(CXSBaseModel):
    __tablename__ = "account"
    id: Mapped[str] = mapped_column(primary_key=True, server_default=text("uuid_generate_v4()"))

    name: Mapped[str]
    logo: Mapped[str]
    plan: Mapped[str]
    country: Mapped[str]
    company_name: Mapped[str]
    industry: Mapped[str]

    partition: Mapped[str]
    active: Mapped[bool]
    is_data_provider: Mapped[bool]

    organization_gid: Mapped[str]
    stripe_customer_id: Mapped[str]
    stripe_subscription_id: Mapped[str]
    data_provider_id: Mapped[str]

    api_keys: Mapped[Optional[List["ApiKey"]]] = relationship(
        back_populates="account", lazy="selectin"
    )
    write_keys: Mapped[Optional[List["WriteKey"]]] = relationship(
        back_populates="account", lazy="selectin"
    )
    users: Mapped[Optional[List["User"]]] = relationship(
        secondary="account_users", back_populates="accounts"
    )

    account_users: Mapped[Optional[List["AccountUser"]]] = relationship(
        back_populates="account", lazy="selectin"
    )
    prompts: Mapped[Optional[List["CustomPrompt"]]] = relationship(
        back_populates="account", lazy="selectin"
    )
    scripts: Mapped[Optional[List["CustomScript"]]] = relationship()
    datasets: Mapped[Optional[List["CustomDataset"]]] = relationship()
    linked_solutions: Mapped[Optional[List["SolutionLink"]]] = relationship()
    components: Mapped[Optional[List["Component"]]] = relationship()

    services: Mapped[Optional[List["Service"]]] = relationship(
        back_populates="account", lazy="selectin"
    )
    solutions: Mapped[Optional[List["Solution"]]] = relationship(
        secondary="solution_link", back_populates="accounts"
    )


class User(CXSBaseModel):
    __tablename__ = "user"

    id: Mapped[str] = Column(primary_key=True, server_default=text("uuid_generate_v4()"))

    name: Mapped[str]
    email: Mapped[str]

    password: Mapped[str]
    f_2fa_enabled: Mapped[bool] = Column(name="2fa_enabled")
    f_2fa_secret: Mapped[str] = Column(name="2fa_secret")
    f_2fa_backup_code: Mapped[str] = Column(name="2fa_backup_code")

    facebook_id: Mapped[str]
    twitter_id: Mapped[str]
    linkedin_id: Mapped[str]
    google_id: Mapped[str]
    github_id: Mapped[str]
    azuread_openidconnect_id: Mapped[str] = Column(name="azuread-openidconnect_id")

    default_account: Mapped[str]

    language: Mapped[str]
    department: Mapped[str]
    role: Mapped[str]
    first_name: Mapped[str]
    last_name: Mapped[str]

    disabled: Mapped[bool]

    tools_spreadsheet: Mapped[bool]
    tools_analytical: Mapped[bool]
    tools_bi: Mapped[bool]
    tools_pipelines: Mapped[bool]

    date_created: Mapped[datetime]
    last_active: Mapped[datetime]

    api_keys: Mapped[Optional[List["ApiKey"]]] = relationship(
        back_populates="user", lazy="selectin"
    )
    user_accounts: Mapped[Optional[List["AccountUser"]]] = relationship(
        back_populates="user", lazy="selectin"
    )

    accounts: Mapped[List["Account"]] = relationship(
        secondary="account_users", back_populates="users"
    )

    service_access: Mapped[Optional[List["ServiceAccess"]]] = relationship()


class ApiKey(CXSBaseModel):

    __tablename__ = "api_key"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, server_default=text("uuid_generate_v4()")
    )

    name: Mapped[str]
    key: Mapped[str]

    client_id: Mapped[UUID]
    client_secret: Mapped[str]

    provisioning_scopes: Mapped[str]
    graph_api_scopes: Mapped[str]
    active: Mapped[bool]
    tags: Mapped[str]

    date_created: Mapped[datetime]

    account_id: Mapped[str] = mapped_column(ForeignKey("account.id"))
    account: Mapped["Account"] = relationship(back_populates="api_keys")

    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"))
    user: Mapped["User"] = relationship(back_populates="api_keys")


class WriteKey(CXSBaseModel):
    __tablename__ = "write_key"

    id: Mapped[str] = Column(primary_key=True, server_default=text("uuid_generate_v4()"))

    key: Mapped[str]
    description: Mapped[str]
    tags: Mapped[str]
    setting = Column(mutable_json_type(JSONB, nested=True))

    source_subscription_id: Mapped[str]
    partition: Mapped[str]

    enabled: Mapped[str]
    date_created: Mapped[str]
    active_from: Mapped[str]
    active_until: Mapped[str]

    account_id: Mapped[str] = mapped_column(ForeignKey("account.id"))
    account: Mapped["Account"] = relationship()  # back_populates="api_keys"


class ServiceType(CXSBaseModel):
    __tablename__ = "service_type"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuid_generate_v4()"))

    name: Mapped[str]
    slug: Mapped[str]

    active: Mapped[bool] = mapped_column(default=True)
    public: Mapped[bool] = mapped_column(default=False)
    internal: Mapped[bool] = mapped_column(default=False)

    date_created: Mapped[datetime] = mapped_column(default=datetime.now)
    active_from: Mapped[datetime] = mapped_column(default=datetime.now)
    active_until: Mapped[datetime]

    services: Mapped[List["Service"]] = relationship(back_populates="service_type")


class Service(CXSBaseModel):
    __tablename__ = "service"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuid_generate_v4()"))

    service_type_id: Mapped[UUID] = mapped_column(ForeignKey("service_type.id"))
    service_type: Mapped["ServiceType"] = relationship(back_populates="services")

    account_id: Mapped[str] = mapped_column(ForeignKey("account.id"))
    account: Mapped["Account"] = relationship(back_populates="services")

    core_service_id: Mapped[UUID] = mapped_column(ForeignKey("service.id"), index=True)
    core_service: Mapped["Service"] = relationship(back_populates="sub_services", lazy="selectin")
    sub_services: Mapped[Optional[List["Service"]]] = relationship()

    name: Mapped[str]
    slug: Mapped[str]
    display_group: Mapped[str]
    description: Mapped[str]
    documentation: Mapped[str]
    doc_url: Mapped[str]

    icon: Mapped[str]
    ui_settings = Column(mutable_json_type(JSONB, nested=True))
    settings = Column(mutable_json_type(JSONB, nested=True))
    layout = Column(mutable_json_type(JSONB, nested=True))

    active: Mapped[bool] = mapped_column(default=True)
    team_access: Mapped[bool] = mapped_column(default=True)
    visibility: Mapped[str] = mapped_column(default="A")
    can_be_deleted: Mapped[bool] = mapped_column(default=False)

    current_version: Mapped[float] = mapped_column(default=25.01)

    service_components: Mapped["ServiceComponent"] = relationship()
    user_access: Mapped[Optional[List["ServiceAccess"]]] = relationship()
    component_links: Mapped[Optional[List["ServiceComponentLink"]]] = relationship()
    linked_solutions: Mapped[Optional[List["SolutionLink"]]] = relationship()

    date_created: Mapped[datetime] = mapped_column(default=datetime.now)
    active_from: Mapped[datetime] = mapped_column(default=datetime.now)
    active_until: Mapped[datetime]


class ServiceAccess(CXSBaseModel):
    __tablename__ = "service_access"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuid_generate_v4()"))

    service_id: Mapped[UUID] = mapped_column(ForeignKey("service.id"))
    service: Mapped["Service"] = relationship(back_populates="user_access")

    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"))
    user: Mapped["User"] = relationship(back_populates="service_access")

    access_type: Mapped[str]
    active: Mapped[bool] = mapped_column(default=True)
    active_from: Mapped[datetime] = mapped_column(default=datetime.now)
    active_until: Mapped[datetime]


class Component(CXSBaseModel):
    __tablename__ = "component"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuid_generate_v4()"))

    account_id: Mapped[Optional[str]] = mapped_column(ForeignKey("account.id"))
    account: Mapped["Account"] = relationship(back_populates="components")

    solution_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("solution.id"))
    solution: Mapped["Solution"] = relationship(back_populates="components")

    name: Mapped[str]
    slug: Mapped[str]

    component_group: Mapped[str]
    component_type: Mapped[str]
    component_variant: Mapped[str]

    icon: Mapped[str]

    public: Mapped[bool] = mapped_column(default=True)
    can_be_modified: Mapped[bool] = mapped_column(default=True)

    description: Mapped[str]
    documentation: Mapped[str]
    documentation_url: Mapped[str]

    core_settings = Column(mutable_json_type(JSONB, nested=True))
    json_schema = Column(mutable_json_type(JSONB, nested=True))
    ui_schema = Column(mutable_json_type(JSONB, nested=True))

    current_version: Mapped[float] = mapped_column(default=25.01)

    component_services: Mapped["ServiceComponent"] = relationship()

    date_created: Mapped[datetime] = mapped_column(default=datetime.now)
    active_from: Mapped[datetime] = mapped_column(default=datetime.now)
    active_until: Mapped[datetime]


class ServiceComponent(CXSBaseModel):
    __tablename__ = "service_component"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuid_generate_v4()"))

    service_id: Mapped[UUID] = mapped_column(ForeignKey("service.id"))
    service: Mapped["Service"] = relationship(back_populates="service_components")

    component_id: Mapped[UUID] = mapped_column(ForeignKey("component.id"))
    component: Mapped["Component"] = relationship(back_populates="component_services")

    component_version: Mapped[float] = mapped_column(default=24.01)

    label: Mapped[str]
    slug: Mapped[str]

    description: Mapped[str]
    icon: Mapped[str]

    active: Mapped[bool] = mapped_column(default=True)

    settings = Column(mutable_json_type(JSONB, nested=True))
    outbound_connection = Column(mutable_json_type(JSONB, nested=True))

    prompts: Mapped[Optional[List["ServiceComponentPrompt"]]] = relationship()
    datasets: Mapped[Optional[List["ServiceComponentDataset"]]] = relationship()
    scripts: Mapped[Optional[List["ServiceComponentScript"]]] = relationship()
    documents: Mapped[Optional[List["ServiceComponentDocument"]]] = relationship()

    out_links: Mapped[Optional[List["ServiceComponentLink"]]] = relationship(
        foreign_keys="ServiceComponentLink.out_serv_comp_id"
    )
    in_links: Mapped[Optional[List["ServiceComponentLink"]]] = relationship(
        foreign_keys="ServiceComponentLink.in_serv_comp_id"
    )

    date_created: Mapped[datetime] = mapped_column(default=datetime.now)


class CustomPrompt(CXSBaseModel):
    __tablename__ = "custom_prompt"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuid_generate_v4()"))

    account_id: Mapped[str] = mapped_column(ForeignKey("account.id"))
    account: Mapped["Account"] = relationship(back_populates="prompts")

    name: Mapped[str]
    prompt: Mapped[str]
    settings = Column(mutable_json_type(JSONB, nested=True))

    active: Mapped[bool] = mapped_column(default=True)
    archived: Mapped[bool] = mapped_column(default=False)
    reusable: Mapped[bool] = mapped_column(default=False)

    service_components: Mapped[Optional[List["ServiceComponentPrompt"]]] = relationship()

    date_created: Mapped[datetime] = mapped_column(default=datetime.now)
    active_from: Mapped[datetime] = mapped_column(default=datetime.now)
    active_until: Mapped[datetime]


class ServiceComponentPrompt(CXSBaseModel):
    __tablename__ = "service_component_prompt"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuid_generate_v4()"))

    service_component_id: Mapped[UUID] = mapped_column(ForeignKey("service_component.id"))
    service_component: Mapped["ServiceComponent"] = relationship(back_populates="prompts")

    custom_prompt_id: Mapped[UUID] = mapped_column(ForeignKey("custom_prompt.id"))
    custom_prompt: Mapped["CustomPrompt"] = relationship(back_populates="service_components")

    ordering: Mapped[int] = mapped_column(default=0)
    settings = Column(mutable_json_type(JSONB, nested=True))

    date_created: Mapped[datetime] = mapped_column(default=datetime.now)
    active_from: Mapped[datetime] = mapped_column(default=datetime.now)
    active_until: Mapped[datetime]


class CustomDataset(CXSBaseModel):
    __tablename__ = "custom_dataset"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuid_generate_v4()"))

    account_id: Mapped[str] = mapped_column(ForeignKey("account.id"))
    account: Mapped["Account"] = relationship(back_populates="datasets")

    name: Mapped[str]
    type: Mapped[str]

    json_schema = Column(mutable_json_type(JSONB, nested=True))
    ui_schema = Column(mutable_json_type(JSONB, nested=True))
    local_data = Column(mutable_json_type(JSONB, nested=True))

    database_type: Mapped[str]
    username: Mapped[str]
    password: Mapped[str]
    connect_url: Mapped[str]
    connection_params = Column(mutable_json_type(JSONB, nested=True))
    setting = Column(mutable_json_type(JSONB, nested=True))

    airtable_app_id: Mapped[str]
    airtable_table_id: Mapped[str]
    airtable_view_id: Mapped[str]
    airtable_api_key: Mapped[str]

    active: Mapped[bool] = mapped_column(default=True)
    archived: Mapped[bool] = mapped_column(default=False)
    reusable: Mapped[bool] = mapped_column(default=False)

    service_components: Mapped["ServiceComponentDataset"] = relationship()

    date_created: Mapped[datetime] = mapped_column(default=datetime.now)
    active_from: Mapped[datetime] = mapped_column(default=datetime.now)
    active_until: Mapped[datetime]


class ServiceComponentDataset(CXSBaseModel):
    __tablename__ = "service_component_dataset"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuid_generate_v4()"))

    service_component_id: Mapped[UUID] = mapped_column(ForeignKey("service_component.id"))
    service_component: Mapped["ServiceComponent"] = relationship(back_populates="datasets")

    custom_dateset_id: Mapped[UUID] = mapped_column(ForeignKey("custom_dataset.id"))
    custom_dataset: Mapped["CustomDataset"] = relationship(back_populates="service_components")

    active: Mapped[bool] = mapped_column(default=True)

    date_created: Mapped[datetime] = mapped_column(default=datetime.now)
    active_from: Mapped[datetime] = mapped_column(default=datetime.now)
    active_until: Mapped[datetime]


class CustomScript(CXSBaseModel):
    __tablename__ = "custom_script"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuid_generate_v4()"))

    account_id: Mapped[str] = mapped_column(ForeignKey("account.id"))
    account: Mapped["Account"] = relationship(back_populates="scripts")

    name: Mapped[str]
    script_type: Mapped[str]

    declaration: Mapped[str]
    documentation: Mapped[str]
    script: Mapped[str]

    prompt: Mapped[str]
    input_schema = Column(mutable_json_type(JSONB, nested=True))
    output_schema = Column(mutable_json_type(JSONB, nested=True))

    settings = Column(mutable_json_type(JSONB, nested=True))

    reusable: Mapped[bool] = mapped_column(default=False)
    version: Mapped[int] = mapped_column(default=0)

    service_components: Mapped["ServiceComponentScript"] = relationship()

    date_created: Mapped[datetime] = mapped_column(default=datetime.now)
    active_from: Mapped[datetime] = mapped_column(default=datetime.now)
    active_until: Mapped[datetime]


class ServiceComponentScript(CXSBaseModel):
    __tablename__ = "service_component_script"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuid_generate_v4()"))

    service_component_id: Mapped[UUID] = mapped_column(ForeignKey("service_component.id"))
    service_component: Mapped["ServiceComponent"] = relationship(back_populates="scripts")

    custom_script_id: Mapped[UUID] = mapped_column(ForeignKey("custom_script.id"))
    custom_script: Mapped["CustomScript"] = relationship(back_populates="service_components")

    ordering: Mapped[int] = mapped_column(default=0)
    settings = Column(mutable_json_type(JSONB, nested=True))

    active: Mapped[bool] = mapped_column(default=True)

    date_created: Mapped[datetime] = mapped_column(default=datetime.now)
    active_from: Mapped[datetime] = mapped_column(default=datetime.now)
    active_until: Mapped[datetime]


class ServiceComponentDocument(CXSBaseModel):
    __tablename__ = "service_component_document"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuid_generate_v4()"))

    service_component_id: Mapped[UUID] = mapped_column(ForeignKey("service_component.id"))
    service_component: Mapped["ServiceComponent"] = relationship(back_populates="documents")

    document_gid: Mapped[UUID]

    settings = Column(mutable_json_type(JSONB, nested=True))
    rule: Mapped[str] = mapped_column(default="WL")
    active: Mapped[bool] = mapped_column(default=True)

    date_created: Mapped[datetime] = mapped_column(default=datetime.now)
    active_from: Mapped[datetime] = mapped_column(default=datetime.now)
    active_until: Mapped[datetime]


class ServiceComponentLink(CXSBaseModel):
    __tablename__ = "service_component_link"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuid_generate_v4()"))

    service_id: Mapped[UUID] = mapped_column(ForeignKey("service.id"))
    service: Mapped["Service"] = relationship(back_populates="component_links")

    out_serv_comp_id: Mapped[UUID] = mapped_column(ForeignKey("service_component.id"))
    out_serv_comp: Mapped["ServiceComponent"] = relationship(
        back_populates="out_links", foreign_keys=[out_serv_comp_id]
    )
    out_port: Mapped[str]

    in_serv_comp_id: Mapped[UUID] = mapped_column(ForeignKey("service_component.id"))
    in_serv_comp: Mapped["ServiceComponent"] = relationship(
        back_populates="in_links", foreign_keys=[in_serv_comp_id]
    )
    in_port: Mapped[str]

    settings = Column(mutable_json_type(JSONB, nested=True))
    active: Mapped[bool] = mapped_column(default=True)

    date_created: Mapped[datetime] = mapped_column(default=datetime.now)
    active_from: Mapped[datetime] = mapped_column(default=datetime.now)
    active_until: Mapped[datetime]


class SolutionCategory(CXSBaseModel):

    __tablename__ = "solution_category"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuid_generate_v4()"))

    name: Mapped[str]
    slug: Mapped[str]
    abbreviation: Mapped[str]

    icon: Mapped[Optional[str]]
    logo: Mapped[Optional[str]]

    parent_category_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("solution_category.id"))
    parent_category: Mapped[Optional["SolutionCategory"]] = relationship(
        back_populates="sub_categories"
    )
    sub_categories: Mapped[Optional[List["SolutionCategory"]]] = relationship()

    internal: Mapped[bool] = mapped_column(default=False)
    active: Mapped[bool] = mapped_column(default=True)

    description: Mapped[Optional[str]]
    documentation: Mapped[Optional[str]]
    documentation_url: Mapped[Optional[str]]

    classifications: Mapped[Optional["SolutionClassification"]] = relationship()
    solutions: Mapped[Optional[List["Solution"]]] = relationship(
        secondary="solution_classification", back_populates="categories"
    )

    date_created: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    active_from: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    active_until: Mapped[Optional[datetime]]


class Solution(CXSBaseModel):

    __tablename__ = "solution"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuid_generate_v4()"))

    name: Mapped[str]
    label: Mapped[Optional[str]]
    brand: Mapped[Optional[str]]

    slug: Mapped[Optional[str]]
    icon: Mapped[Optional[str]]
    logo: Mapped[Optional[str]]

    url: Mapped[Optional[str]]

    event_source: Mapped[bool] = mapped_column(default=False)

    settings_ui_schema = Column(mutable_json_type(JSONB, nested=True))
    auth_ui_schema = Column(mutable_json_type(JSONB, nested=True))
    settings = Column(mutable_json_type(JSONB, nested=True))

    active: Mapped[bool] = mapped_column(default=False)
    ready: Mapped[bool] = mapped_column(default=False)
    internal: Mapped[bool] = mapped_column(default=False)

    description: Mapped[Optional[str]]
    documentation: Mapped[Optional[str]]
    documentation_url: Mapped[Optional[str]]

    variants: Mapped["SolutionVariant"] = relationship()
    pricing: Mapped["SolutionPricing"] = relationship()
    classifications: Mapped["SolutionClassification"] = relationship()
    solution_links: Mapped["SolutionLink"] = relationship()

    categories: Mapped[Optional[List["SolutionCategory"]]] = relationship(
        secondary="solution_classification", back_populates="solutions"
    )
    accounts: Mapped[Optional[List["Account"]]] = relationship(
        secondary="solution_link", back_populates="solutions"
    )
    components: Mapped["Component"] = relationship(back_populates="solution")

    date_created: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    active_from: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    active_until: Mapped[Optional[datetime]]


class SolutionVariant(CXSBaseModel):

    __tablename__ = "solution_variant"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuid_generate_v4()"))

    solution_id: Mapped[UUID] = mapped_column(ForeignKey("solution.id"))
    solution: Mapped["Solution"] = relationship(back_populates="variants")

    name: Mapped[str]
    slug: Mapped[str]

    pricing: Mapped["SolutionPricing"] = relationship()

    date_created: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    active_from: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    active_until: Mapped[Optional[datetime]]


class SolutionPricing(CXSBaseModel):

    __tablename__ = "solution_pricing"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuid_generate_v4()"))

    solution_id: Mapped[UUID] = mapped_column(ForeignKey("solution.id"))
    solution: Mapped["Solution"] = relationship(back_populates="pricing")

    solution_variant_id: Mapped[UUID] = mapped_column(ForeignKey("solution_variant.id"))
    solution_variant: Mapped["SolutionVariant"] = relationship(back_populates="pricing")

    ui_settings = Column(mutable_json_type(JSONB, nested=True))

    date_created: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    active_from: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    active_until: Mapped[Optional[datetime]]


class SolutionClassification(CXSBaseModel):

    __tablename__ = "solution_classification"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuid_generate_v4()"))

    solution_id: Mapped[UUID] = mapped_column(ForeignKey("solution.id"))
    solution: Mapped["Solution"] = relationship(back_populates="classifications")

    solution_category_id: Mapped[UUID] = mapped_column(ForeignKey("solution_category.id"))
    solution_category: Mapped["SolutionCategory"] = relationship(back_populates="classifications")

    primary_category: Mapped[bool] = mapped_column(default=False)
    active: Mapped[bool] = mapped_column(default=False)

    settings = Column(mutable_json_type(JSONB, nested=True))

    date_created: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    active_from: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    active_until: Mapped[Optional[datetime]]


class SolutionLink(CXSBaseModel):

    __tablename__ = "solution_link"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuid_generate_v4()"))

    account_id: Mapped[str] = mapped_column(ForeignKey("account.id"))
    account: Mapped["Account"] = relationship(back_populates="linked_solutions")

    solution_id: Mapped[UUID] = mapped_column(ForeignKey("solution.id"))
    solution: Mapped["Solution"] = relationship(back_populates="solution_links")

    service_id: Mapped[UUID] = mapped_column(ForeignKey("service.id"))
    service: Mapped["Service"] = relationship(back_populates="linked_solutions")

    account_name: Mapped[str]
    username: Mapped[str]
    connect_url: Mapped[str]

    password: Mapped[str]
    api_key: Mapped[str]
    certificate: Mapped[str]
    headers = Column(mutable_json_type(JSONB, nested=True))

    settings = Column(mutable_json_type(JSONB, nested=True))
    custom_pricing = Column(mutable_json_type(JSONB, nested=True))

    occurs_cost: Mapped[bool] = mapped_column(default=False)
    log_usage: Mapped[bool] = mapped_column(default=False)
    active: Mapped[bool] = mapped_column(default=True)
    archived: Mapped[bool] = mapped_column(default=False)
    reusable: Mapped[bool] = mapped_column(default=False)

    date_created: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    active_from: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    active_until: Mapped[Optional[datetime]]
