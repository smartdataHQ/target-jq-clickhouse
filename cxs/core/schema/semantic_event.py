import enum
import json
import logging
import uuid
from datetime import datetime
from typing import Annotated, Any, Dict, Optional, cast

import pydantic
from pydantic import BaseModel, Field, model_validator

from cxs.core.schema import CXSBase, OmitIfNone, empty_dict, empty_list
from cxs.core.utils.event_utils import calculate_event_id

logger = logging.getLogger(__name__)


class EventType(enum.Enum):
    track = "track"
    page = "page"
    screen = "screen"
    identify = "identify"
    group = "group"


class Involved(CXSBase):
    label: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Label of the involved entity",
        default="",
    )
    role: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Role of the involved entity",
        default="",
    )
    entity_type: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Type of the involved entity",
        default="",
    )
    entity_gid: Annotated[Optional[uuid.UUID], OmitIfNone()] = Field(description="Entity gid", default=None)
    id: Annotated[Optional[str], OmitIfNone()] = Field(description="Id of the involved entity", default="")
    id_type: Annotated[Optional[str], OmitIfNone()] = Field(description="Type of the id", default="")
    capacity: Annotated[Optional[float], OmitIfNone()] = Field(
        description="Capacity of the involved entity",
        default=0.0,
    )

    @model_validator(mode="before")
    def pre_init(cls, values):

        if values.get("entity_gid") and isinstance(values.get("entity_gid"), str):
            values["entity_gid"] = uuid.UUID(values.get("entity_gid"))

        if values.get("entity_gid") == uuid.UUID("00000000-0000-0000-0000-000000000000"):
            del values["entity_gid"]

        values["id"] = str(values.get("id"))

        return values


class Classification(CXSBase):
    type: Annotated[Optional[str], OmitIfNone()] = Field(..., description="Type of the classification")
    value: Annotated[Optional[str], OmitIfNone()] = Field(..., description="Value of the classification")
    reasoning: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Reasoning for the classification",
        default="",
    )
    score: Annotated[Optional[float], OmitIfNone()] = Field(
        description="Score of the classification",
        default=0,
    )
    confidence: Annotated[Optional[float], OmitIfNone()] = Field(
        description="Confidence of the classification",
        default=0.0,
    )
    weight: Annotated[Optional[float], OmitIfNone()] = Field(
        description="Score of the classification",
        default=0.0,
    )


class Sentiment(CXSBase):
    type: Annotated[Optional[str], OmitIfNone()] = Field(..., description="Type of the sentiment")
    sentiment: Annotated[Optional[str], OmitIfNone()] = Field(..., description="Type of the sentiment")
    entity_type: Annotated[Optional[str], OmitIfNone()] = Field(description="Type of the entity", default="")
    entity_gid: Annotated[Optional[uuid.UUID], OmitIfNone()] = Field(description="Entity gid", default="")
    id_type: Annotated[Optional[str], OmitIfNone()] = Field(description="Type of the id", default="")
    id: Annotated[Optional[str], OmitIfNone()] = Field(description="Id of the entity", default="")
    target_category: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Category of the target",
        default="",
    )
    target_type: Annotated[Optional[str], OmitIfNone()] = Field(description="Type of the target", default="")
    target_entity: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Entity of the target",
        default="",
    )
    reason: Annotated[Optional[str], OmitIfNone()] = Field(description="Reason for the sentiment", default="")


class Analysis(CXSBase):
    item: Annotated[Optional[str], OmitIfNone()] = Field(..., description="Item of the analysis")
    provider: Annotated[Optional[str], OmitIfNone()] = Field(..., description="Provider of the analysis")
    variant: Annotated[Optional[str], OmitIfNone()] = Field(..., description="Variant of the analysis")
    token_in: Annotated[Optional[int], OmitIfNone()] = Field(..., description="Token in of the analysis")
    token_out: Annotated[Optional[int], OmitIfNone()] = Field(..., description="Token out of the analysis")
    amount: Annotated[Optional[float], OmitIfNone()] = Field(
        description="The cost of the analysis",
        default=0.0,
    )
    processing_time: Annotated[Optional[float], OmitIfNone()] = Field(
        description="Processing time of the analysis",
        default=0.0,
    )
    currency: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Currency of the analysis",
        default="USD",
    )

    @model_validator(mode="before")
    def pre_init(cls, values):
        if not values.get("token_in"):
            logger.warning("token_in missing for values: %s", str(values))

        return values


class Location(CXSBase):
    location_of: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The type of location (e.g. 'Customer', 'Supplier', 'Postal Address', 'Business Address', 'Home Address', 'Other')",
        default="",
    )
    label: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The label of the location (e.g. 'Street name 1, 1234')",
        default="",
    )
    country: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The name of the country (e.g.'Iceland')",
        default="",
    )
    country_code: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The country code (e.g. 'IS')",
        default="",
    )
    code: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The code of the location (e.g. '1234')",
        default="",
    )
    region: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The region of the location (e.g. 'Gullbringu og kjósarsýsla')",
        default="",
    )
    division: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The division of the location (e.g. 'Capital Region')",
        default="",
    )
    municipality: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The municipality of the location (e.g. 'Reykjavik')",
        default="",
    )
    locality: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The locality of the location (e.g. 'Vesturbær')",
        default="",
    )
    postal_code: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The postal code of the location (e.g. '101')",
        default="",
    )
    postal_name: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The name of the postal code (e.g. 'Vesturbær')",
        default="",
    )
    street: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The street of the location (e.g. 'Laugavegur')",
        default="",
    )
    street_nr: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The street number of the location (e.g. '1')",
        default=None,
    )
    address: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The address of the location (e.g. 'Laugavegur 1, 101 Reykjavik')",
        default="",
    )
    longitude: Annotated[Optional[float], OmitIfNone()] = Field(
        description="The longitude of the location (e.g. -21.9333)",
        default=None,
    )
    latitude: Annotated[Optional[float], OmitIfNone()] = Field(
        description="The latitude of the location (e.g. 64.1355)",
        default=None,
    )
    geohash: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The geohash of the location (e.g. 'gcpuv')",
        default="",
    )
    duration_from: Annotated[Optional[datetime], OmitIfNone()] = Field(
        description="The start date of the location (e.g. '2022-01-01 00:00:00') Used if the location is temporary",
        default=None,
    )
    duration_until: Annotated[Optional[datetime], OmitIfNone()] = Field(
        description="The end date of the location (e.g. '2022-01-01 00:00:00') Used if the location is temporary",
        default=None,
    )


class Product(CXSBase):
    position: Annotated[Optional[int], OmitIfNone()] = Field(
        description="Position in the product list (ex. 3)",
        default=None,
    )
    entry_type: Annotated[Optional[str], OmitIfNone()] = Field(
        description="'Cart Item', 'Line Item', 'Wishlist', 'Recommendation', 'Purchase Order', 'Search Results', 'Other', 'Delivery', 'Reservation'",
        default="",
    )
    line_id: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Unique ID for the line item",
        default="",
    )

    product_id: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Database id of the product being purchases",
        default="",
    )
    entity_gid: Annotated[Optional[uuid.UUID], OmitIfNone()] = Field(
        description="Database id of the product being purchases",
        default=None,
    )

    sku: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Sku of the product being purchased",
        default="",
    )
    barcode: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Barcode of the product being purchased",
        default="",
    )
    gtin: Annotated[Optional[str], OmitIfNone()] = Field(
        description="GTIN of the product being purchased",
        default="",
    )
    upc: Annotated[Optional[str], OmitIfNone()] = Field(
        description="UPC of the product being purchased",
        default="",
    )
    ean: Annotated[Optional[str], OmitIfNone()] = Field(
        description="EAN of the product being purchased",
        default="",
    )
    isbn: Annotated[Optional[str], OmitIfNone()] = Field(
        description="ISBN of the product being purchased",
        default="",
    )
    serial_number: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Serial number of the product being purchased",
        default="",
    )
    supplier_number: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Supplier number of the product being purchased",
        default="",
    )
    tpx_serial_number: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Serial number of the product being purchased issued by a third party (not GS1)",
        default="",
    )

    bundle_id: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The ID of the bundle the product belongs to when listing all products in a bundle",
        default="",
    )
    bundle: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The name of the bundle the product belongs to",
        default="",
    )
    product: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Name of the product being viewed",
        default="",
    )
    variant: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Variant of the product being purchased",
        default="",
    )
    novelty: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Novelty of the product being purchased",
        default="",
    )
    size: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Size of the product being purchased",
        default="",
    )
    packaging: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Packaging of the product being purchased",
        default="",
    )
    condition: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Condition of the product being purchased",
        default="",
    )
    ready_for_use: Annotated[Optional[bool], OmitIfNone()] = Field(
        description="If the product is ready for use",
        default=None,
    )
    core_product: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The core product being purchased",
        default="",
    )
    origin: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Location identifier for the origin of the product being purchased",
        default="",
    )
    brand: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Brand associated with the product",
        default="",
    )
    product_line: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Product line associated with the product",
        default="",
    )
    own_product: Annotated[Optional[bool], OmitIfNone()] = Field(
        description="If the item is a store brand",
        default=None,
    )
    product_dist: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Product Distribution is used to track the distribution class of the product (e.g. 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J')",
        default="",
    )

    main_category: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Product category being purchased",
        default="",
    )
    main_category_id: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Product category ID being purchased",
        default="",
    )
    category: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Name of the sub-category of the product being purchased",
        default="",
    )
    category_id: Annotated[Optional[str], OmitIfNone()] = Field(
        description="ID of the sub-category of the product being purchased",
        default="",
    )
    income_category: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Income category of the product being purchased",
        default="",
    )

    gs1_brick_id: Annotated[Optional[str], OmitIfNone()] = Field(
        description="GS1 Brick ID of the product being purchased",
        default="",
    )
    gs1_brick: Annotated[Optional[str], OmitIfNone()] = Field(
        description="GS1 Brick Name of the product being purchased",
        default="",
    )
    gs1_brick_short: Annotated[Optional[str], OmitIfNone()] = Field(
        description="GS1 Brick Short Name",
        default="",
    )
    gs1_brick_variant: Annotated[Optional[str], OmitIfNone()] = Field(
        description="GS1 Brick Variant",
        default="",
    )
    gs1_conditions: Annotated[Optional[str], OmitIfNone()] = Field(
        description="GS1 Brick Conditions",
        default="",
    )
    gs1_processed: Annotated[Optional[str], OmitIfNone()] = Field(
        description="GS1 Brick Processed",
        default="",
    )
    gs1_consumable: Annotated[Optional[str], OmitIfNone()] = Field(
        description="GS1 Brick Processed",
        default="",
    )
    gs1_class: Annotated[Optional[str], OmitIfNone()] = Field(description="GS1 Class", default="")
    gs1_family: Annotated[Optional[str], OmitIfNone()] = Field(description="GS1 Family", default="")
    gs1_segment: Annotated[Optional[str], OmitIfNone()] = Field(description="GS1 Segment", default="")

    starts: Annotated[Optional[datetime], OmitIfNone()] = Field(
        description="Start date for the product being purchased",
        default=None,
    )
    ends: Annotated[Optional[datetime], OmitIfNone()] = Field(
        description="End date for the product being purchased",
        default=None,
    )
    duration: Annotated[Optional[float], OmitIfNone()] = Field(
        description="Duration for the product being purchased in minutes",
        default=None,
    )
    seats: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Seats assignments for the product being purchased",
        default="",
    )
    destination: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Location identifier for the destination of the product being purchased",
        default="",
    )
    lead_time: Annotated[Optional[float], OmitIfNone()] = Field(
        description="Lead time in days from the product being purchased until it's delivered (from purchase data to delivery date)",
        default=None,
    )

    dwell_time_ms: Annotated[Optional[int], OmitIfNone()] = Field(
        description="The time that this product was in the viewport of the customer (above the fold)",
        default=None,
    )

    supplier: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Supplier of the product being purchased",
        default="",
    )
    supplier_id: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Supplier ID of the product being purchased",
        default="",
    )
    manufacturer: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Manufacturer of the product being purchased",
        default="",
    )
    manufacturer_id: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Manufacturer ID of the product being purchased",
        default="",
    )
    promoter: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Promoter of the product being purchased",
        default="",
    )
    promoter_id: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Promoter ID of the product being purchased",
        default="",
    )
    product_mgr_id: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Product Manager ID of the product being purchased",
        default="",
    )
    product_mgr: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Product Manager of the product being purchased",
        default="",
    )

    units: Annotated[Optional[float], OmitIfNone()] = Field(
        description="Product units (1 if sold by weight)",
        default=None,
    )
    unit_size: Annotated[Optional[float], OmitIfNone()] = Field(
        description="The quantity of each unit",
        default=None,
    )
    uom: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Unit of measure of the product(s) being purchased (Weight, Duration, Items, Volume, etc.)",
        default="",
    )
    unit_price: Annotated[Optional[float], OmitIfNone()] = Field(
        description="Price ($) of the product being purchased",
        default=None,
    )
    unit_cost: Annotated[Optional[float], OmitIfNone()] = Field(
        description="Cost ($) of the product being purchased",
        default=None,
    )
    bundled_units: Annotated[Optional[int], OmitIfNone()] = Field(
        description="Number of units in a volume pack or bundle",
        default=None,
    )
    price_bracket: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Price bracket of the product being purchased",
        default="",
    )

    tax_percentage: Annotated[Optional[float], OmitIfNone()] = Field(
        description="Total tax-percentage associated with the product purchase (unit_price * units * tax_rate = tax)",
        default=None,
    )
    discount_percentage: Annotated[Optional[float], OmitIfNone()] = Field(
        description="The discount-percentage applied to the product (unit_price * units * discount_rate = discount)",
        default=None,
    )
    kickback_percentage: Annotated[Optional[float], OmitIfNone()] = Field(
        description="The kickback-percentage applied to the product (unit_price * units * kickback_rate = kickback)",
        default=None,
    )
    commission: Annotated[Optional[float], OmitIfNone()] = Field(
        description="The total commission percentage applied to the product on the line basis (unit_price * units * commission_rate = commission)",
        default=None,
    )
    coupon: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Coupon code associated with a product (for example, MAY_DEALS_3)",
        default="",
    )

    scale_item: Annotated[Optional[bool], OmitIfNone()] = Field(
        description="If the quantity of the product was measured during checkout / at the register",
        default=None,
    )
    price_changed: Annotated[Optional[bool], OmitIfNone()] = Field(
        description="If the price of the product has changed at the register/terminal",
        default=None,
    )
    line_discounted: Annotated[Optional[bool], OmitIfNone()] = Field(
        description="If the line item has a discount",
        default=None,
    )
    url: Annotated[Optional[str], OmitIfNone()] = Field(description="URL of the product page", default="")
    img_url: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Image url of the product",
        default="",
    )


class Commerce(CXSBase):
    details: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Other properties of the commerce event that cannot be mapped to the schema or have complex data types",
        default="",
    )
    checkout_id: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Unique ID for the checkout",
        default="",
    )
    order_id: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Unique ID for the order",
        default="",
    )
    cart_id: Annotated[Optional[str], OmitIfNone()] = Field(description="Unique ID for the cart", default="")
    employee_id: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Unique ID for the employee working the terminal/register",
        default="",
    )
    external_order_id: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Unique External ID for the order",
        default="",
    )
    terminal_id: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Unique External ID for the terminal used for the transaction",
        default="",
    )
    affiliation_id: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Unique ID for the affiliation",
        default="",
    )
    affiliation: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Store or affiliation from which this transaction occurred (for example, Google Store)",
        default="",
    )
    agent: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The Agent responsible for the sale",
        default="",
    )
    agent_id: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The ID of the Agent responsible for the sale",
        default="",
    )
    sold_location: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The location where the sale occurred",
        default="",
    )
    sold_location_id: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The ID of the location where the sale occurred",
        default="",
    )
    business_day: Annotated[Optional[datetime], OmitIfNone()] = Field(
        description="The business day of the transaction",
        default=None,
    )
    revenue: Annotated[Optional[float], OmitIfNone()] = Field(description="Total gross revenue", default=0.0)
    tax: Annotated[Optional[float], OmitIfNone()] = Field(description="Total tax amount", default=0.0)
    discount: Annotated[Optional[float], OmitIfNone()] = Field(
        description="Total discount amount",
        default=0.0,
    )
    cogs: Annotated[Optional[float], OmitIfNone()] = Field(
        description="Total cost of goods sold",
        default=0.0,
    )
    commission: Annotated[Optional[float], OmitIfNone()] = Field(
        description="Total commission amount",
        default=0.0,
    )
    currency: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Currency code associated with the transaction",
        default="",
    )
    exchange_rate: Annotated[Optional[float], OmitIfNone()] = Field(
        description="Currency exchange rate associated with the transaction",
        default=1.0,
    )
    coupon: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Transaction coupon redeemed with the transaction",
        default="",
    )
    payment_type: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Type of payment (ex. Card, Paypal, Cash, etc.)",
        default="",
    )
    payment_sub_type: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Subtype of payment (ex. Visa, Mastercard, etc.)",
        default="",
    )
    payment_details: Annotated[Optional[str], OmitIfNone()] = Field(
        description="Details of the payment (ex. Last 4 digits of the card, etc.)",
        default="",
    )


class Campaign(BaseModel):
    """
    Standard marketing properties as defined by Segment and Google Analytics
    """

    campaign: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The campaign (e.g. 'summer')",
        default="",
    )
    source: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The source (e.g. 'google')",
        default="",
    )
    medium: Annotated[Optional[str], OmitIfNone()] = Field(description="The medium (e.g. 'cpc')", default="")
    term: Annotated[Optional[str], OmitIfNone()] = Field(description="The term (e.g. 'beach')", default="")
    content: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The content (e.g. 'ad1')",
        default="",
    )


class App(BaseModel):
    """
    Application properties as defined by Segment
    """

    build: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The build of the app (e.g. '1.1.0')",
        default="",
    )
    name: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The name of the app (e.g. 'Segment')",
        default="",
    )
    namespace: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The namespace of the app (e.g. 'com.segment.analytics')",
        default="",
    )
    version: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The version of the app (e.g. '1.1.0')",
        default="",
    )


class OS(BaseModel):
    """
    Operating System properties as defined by Segment
    """

    name: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The OS of the device (e.g. 'iOS')",
        default="",
    )
    version: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The OS version of the device (e.g. '9.1')",
        default="",
    )


class UserAgent(BaseModel):
    """
    User Agent properties as defined by Segment
    """

    mobile: Annotated[Optional[bool], OmitIfNone()] = Field(
        description="Whether the user agent is mobile (e.g. 'true')",
        default=None,
    )
    platform: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The platform of the user agent (e.g. 'Apple Mac')",
        default="",
    )
    signature: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The user agent (e.g. 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36')",
        default="",
    )
    data: Annotated[Optional[Dict[str, str]], OmitIfNone()] = Field(
        description="The user agent data (e.g. {'brand': 'Apple', 'version': 'Mac OS X 10_10_5'})",
        default_factory=lambda: empty_dict(),
    )


class Page(BaseModel):
    """
    Page properties as defined by Segment
    """

    encoding: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The encoding of the page (e.g. 'UTF-8')",
        default="",
    )
    host: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The host of the page (e.g. 'segment.com')",
        default="",
    )
    path: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The path of the page (e.g. '/docs')",
        default="",
    )
    referrer: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The referrer of the page (e.g. 'https://segment.com')",
        default="",
    )
    referring_domain: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The referring domain of the page (e.g. 'segment.com')",
        default="",
    )
    search: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The search of the page (e.g. 'segment')",
        default="",
    )
    title: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The title of the page (e.g. 'Analytics.js Quickstart - Segment')",
        default="",
    )
    url: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The url of the page (e.g. 'https://segment.com/docs/connections/sources/catalog/libraries/website/javascript/quickstart/')",
        default="",
    )


class Referrer(BaseModel):
    """
    Referrer properties as defined by Segment
    """

    id: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The referrer ID of the library (e.g. '3c8da4a4-4f4b-11e5-9e98-2f3c942e34c8')",
        default="",
    )
    type: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The referrer type of the library (e.g. 'dataxu')",
        default="",
    )


class Screen(BaseModel):
    """
    Screen properties as defined by Segment
    """

    density: Annotated[Optional[int], OmitIfNone()] = Field(
        description="The density of the screen (e.g. 2)",
        default=None,
    )
    height: Annotated[Optional[int], OmitIfNone()] = Field(
        description="The height of the screen (e.g. 568)",
        default=None,
    )
    width: Annotated[Optional[int], OmitIfNone()] = Field(
        description="The width of the screen (e.g. 320)",
        default=None,
    )
    inner_height: Annotated[Optional[int], OmitIfNone()] = Field(
        description="The inner height of the screen (e.g. 568)",
        default=None,
    )
    inner_width: Annotated[Optional[int], OmitIfNone()] = Field(
        description="The inner width of the screen (e.g. 320)",
        default=None,
    )


class Context(BaseModel):
    """
    Root level event message context properties
    """

    active: Annotated[Optional[bool], OmitIfNone()] = Field(
        description="Whether the library is active (e.g. 'true')",
        default=None,
    )
    ip: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The IP of the user in IPv4 format (e.g. '1')",
        default="",
    )
    ipv6: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The IP of the user in IPv6 format (e.g. '1')",
        default="",
    )
    locale: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The locale used where the event happened (e.g. 'en-US')",
        default="",
    )
    group_id: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The group ID associated with the event (e.g. 'a89d88da-4f4b-11e5-9e98-2f3c942e34c8')",
        default="",
    )
    timezone: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The timezone the event happened in (e.g. 'America/Los_Angeles')",
        default="",
    )
    location: Annotated[Optional[Dict[str, float]], OmitIfNone()] = Field(
        description="The location associated with the event (e.g. {'latitude': 37.7576171, 'longitude': -122.5776844})",
        default_factory=lambda: empty_dict(),
    )


class Library(BaseModel):
    """
    Library properties as defined by Segment
    """

    name: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The name of the library (e.g. 'analytics-ios')",
        default="",
    )
    version: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The version of the library (e.g. '3.0.0')",
        default="",
    )


class Device(BaseModel):
    """
    Device properties as defined by Segment
    """

    ad_tracking_enabled: Annotated[Optional[bool], OmitIfNone()] = Field(
        description="Whether ad tracking is enabled (e.g. 'true')",
        default=None,
    )
    id: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The manufacturer id for the device (e.g. 'e3bcf3f796b9f377284bfbfbcf1f8f92b6')",
        default="",
    )
    version: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The device version (e.g. '9.1')",
        default="",
    )
    mac_address: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The device mac address (e.g. '00:00:00:00:00:00')",
        default="",
    )
    manufacturer: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The manufacturer of the device (e.g. 'Apple')",
        default="",
    )
    model: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The model of the device (e.g. 'iPhone 6')",
        default="",
    )
    name: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The name of the device (e.g. 'Nexus 5')",
        default="",
    )
    type: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The type of the device (e.g. 'ios')",
        default="",
    )
    token: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The token of the device (e.g. 'e3bcf3f796b9f377284bfbfbcf1f8f92b6')",
        default="",
    )
    locale: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The locale of the device (e.g. 'en-US')",
        default="",
    )
    timezone: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The timezone of the device (e.g. 'America/Los_Angeles')",
        default="",
    )
    # advertising_id: Annotated[Optional[str], OmitIfNone()] = Field(description="The advertising ID of the device (e.g. '350e9d90-d7f5-11e4-b9d6-


class Network(BaseModel):
    """
    Network properties as defined by Segment
    """

    cellular: Annotated[Optional[bool], OmitIfNone()] = Field(
        description="Whether the network is cellular (e.g. 'true')",
        default=None,
    )
    bluetooth: Annotated[Optional[bool], OmitIfNone()] = Field(
        description="Whether the network is bluetooth (e.g. 'true')",
        default=None,
    )
    wifi: Annotated[Optional[bool], OmitIfNone()] = Field(
        description="Whether the network is wifi (e.g. 'true')",
        default=None,
    )
    carrier: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The network carrier of the device (e.g. 'Verizon')",
        default="",
    )


class Traits(BaseModel):
    """
    Trait Properties that should be stores separately for GDPR reasons
    The user id should never be the same as the user id in the traits or any other personal identifiable
    information
    """

    id: Annotated[Optional[str], OmitIfNone()] = Field(description="The ID of the user", default="")
    name: Annotated[Optional[str], OmitIfNone()] = Field(description="The name of the user", default="")
    first_name: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The first name of the user",
        default="",
    )
    last_name: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The last name of the user",
        default="",
    )
    social_security_nr: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The social security number of the user",
        default="",
    )
    social_security_nr_family: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The social security number of the user",
        default="",
    )
    email: Annotated[Optional[str], OmitIfNone()] = Field(description="The email of the user", default="")
    phone: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The phone number of the user",
        default="",
    )
    avatar: Annotated[Optional[str], OmitIfNone()] = Field(description="The avatar of the user", default="")
    username: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The username of the user",
        default="",
    )
    website: Annotated[Optional[str], OmitIfNone()] = Field(description="The website of the user", default="")
    age: Annotated[Optional[int], OmitIfNone()] = Field(description="The age of the user", default=None)
    birthday: Annotated[Optional[datetime], OmitIfNone()] = Field(
        description="The birthday of the user",
        default=None,
    )
    created_at: Annotated[Optional[datetime], OmitIfNone()] = Field(
        description="The date the user was created",
        default=None,
    )
    company: Annotated[Optional[str], OmitIfNone()] = Field(description="The company of the user", default="")
    title: Annotated[Optional[str], OmitIfNone()] = Field(description="The title of the user", default="")
    pronouns: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The pronouns of the user",
        default="",
    )
    salutation: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The salutation of the user",
        default="",
    )
    description: Annotated[Optional[str], OmitIfNone()] = Field(
        description="A general description of the user",
        default="",
    )
    industry: Annotated[Optional[str], OmitIfNone()] = Field(
        description="The industry of the user",
        default="",
    )
    employees: Annotated[Optional[int], OmitIfNone()] = Field(
        description="The number of employees of the user",
        default=None,
    )
    plan: Annotated[Optional[str], OmitIfNone()] = Field(description="The plan of the user", default="")
    total_billed: Annotated[Optional[float], OmitIfNone()] = Field(
        description="The total billed of the user",
        default=None,
    )
    logins: Annotated[Optional[int], OmitIfNone()] = Field(
        description="The number of logins of the user",
        default=None,
    )
    address: Annotated[Optional[Dict[str, str]], OmitIfNone()] = Field(
        description="The address of the user",
        default_factory=lambda: empty_dict(),
    )


class SemanticEvent(BaseModel):
    """
    Partial schema for a semantic event that is needed for ticket analysis
    """

    entity_gid: uuid.UUID = Field(
        ...,
        description="Entity gid is the unique identifier of the entity that the event is related to",
    )

    timestamp: datetime = Field(..., description="Timestamp of the event. Iso format 8601")
    type: EventType = Field(..., description="Type of the event")
    event: str = Field(..., description="Name of the event where the last word is a verb in past tense")
    event_gid: uuid.UUID = Field(
        description="Event gid that must be set before saving the event",
        default=None,
    )

    properties: Annotated[Optional[Dict[str, Any]], OmitIfNone()] = Field(
        description="Additional properties of the event",
        default_factory=lambda: empty_dict(),
    )
    involves: Annotated[Optional[list[Involved]], OmitIfNone()] = Field(
        description="Entities involved in the event",
        default_factory=lambda: empty_list(),
    )

    dimensions: Annotated[Optional[Dict[str, str]], OmitIfNone()] = Field(
        description="Dimensions of the event",
        default_factory=lambda: empty_dict(),
    )
    metrics: Annotated[Optional[Dict[str, float]], OmitIfNone()] = Field(
        description="Metrics of the event",
        default_factory=lambda: empty_dict(),
    )
    content: Annotated[Optional[Dict[str, str]], OmitIfNone()] = Field(
        description="Content of the event",
        default_factory=lambda: empty_dict(),
    )
    flags: Annotated[Optional[Dict[str, bool]], OmitIfNone()] = Field(
        description="Flags of the event",
        default_factory=lambda: empty_dict(),
    )

    sentiment: Annotated[Optional[list[Sentiment]], OmitIfNone()] = Field(
        description="Entity sentiment of the event",
        default_factory=lambda: empty_list(),
    )
    classification: Annotated[Optional[list[Classification]], OmitIfNone()] = Field(
        description="Classification of the event",
        default_factory=lambda: empty_list(),
    )
    analysis: Annotated[Optional[list[Analysis]], OmitIfNone()] = Field(
        description="Flags of the event",
        default_factory=lambda: empty_list(),
    )

    analyse: Annotated[Optional[Dict[str, bool]], OmitIfNone()] = Field(
        description="Active analysis",
        default_factory=lambda: empty_dict(),
    )
    integrations: Annotated[Optional[Dict[str, bool]], OmitIfNone()] = Field(
        description="Active integrations",
        default_factory=lambda: empty_dict(),
    )
    underscore_process: Annotated[Optional[Dict[str, Any]], OmitIfNone()] = Field(
        description="Process flags and properties",
        default_factory=lambda: empty_dict(),
    )

    messageId: Annotated[Optional[str], OmitIfNone()] = Field(description="External message ID", default="")
    source: Annotated[Optional[str], OmitIfNone()] = Field(description="Partition of the event", default="")
    partition: str = Field(..., description="Partition of the event")
    sign: int = Field(description="Sign of the event", default=1)

    # many missing properties and nested objects

    @model_validator(mode="before")
    def pre_init(cls, values):

        if "timestamp" not in values or values["timestamp"] is None:
            values["timestamp"] = datetime.now().isoformat()

        if "organization_gid" in values:
            default_gid = values.pop("organization_gid")
            if values.get("entity_gid") is None:
                values["entity_gid"] = default_gid

        if values.get("event_gid") is None or values.get("event_gid") == uuid.UUID(
            "00000000-0000-0000-0000-000000000000"
        ):
            values["event_gid"] = calculate_event_id(event=values)

        for check_uuid in ["entity_gid", "event_gid"]:
            if isinstance(values.get(check_uuid), str):
                values[check_uuid] = uuid.UUID(values.get(check_uuid))

        if values.get("involves.id") is not None:
            involves = []
            idx = 0
            for _ in values.get("involves.id"):
                involves.append(
                    {
                        "label": values.get("involves.label")[idx],
                        "role": values.get("involves.role")[idx],
                        "entity_type": values.get("involves.entity_type")[idx],
                        "entity_gid": values.get("involves.entity_gid")[idx],
                        "id": values.get("involves.id")[idx],
                        "id_type": values.get("involves.id_type")[idx],
                    }
                )
                idx += 1
            values["involves"] = involves

        if values.get("classification.type") is not None:
            classification = []
            idx = 0
            for _ in values.get("classification.type"):
                classification.append(
                    {
                        "type": values.get("classification.type")[idx],
                        "value": values.get("classification.value")[idx],
                        "reasoning": values.get("classification.reasoning")[idx],
                        "score": values.get("classification.score")[idx],
                        "confidence": values.get("classification.confidence")[idx],
                        "weight": values.get("classification.weight")[idx],
                    }
                )
                idx += 1
            values["classification"] = classification

        if values.get("analysis.item") is not None:
            analysis = []
            idx = 0
            for _ in values.get("analysis.item"):
                analysis.append(
                    {
                        "item": values.get("analysis.item")[idx],
                        "provider": values.get("analysis.provider")[idx],
                        "variant": values.get("analysis.variant")[idx],
                        "token_in": values.get("analysis.token_in")[idx],
                        "token_out": values.get("analysis.token_out")[idx],
                        "amount": values.get("analysis.amount")[idx],
                        "processing_time": values.get("analysis.processing_time")[idx],
                        "currency": values.get("analysis.currency")[idx],
                    }
                )
                idx += 1
            values["analysis"] = analysis

        if values.get("sentiment.type") is not None:
            sentiment = []
            idx = 0
            for _ in values.get("sentiment.type"):
                sentiment.append(
                    {
                        "type": values.get("sentiment.type")[idx],
                        "sentiment": values.get("sentiment.sentiment")[idx],
                        "reason": values.get("sentiment.reason")[idx],
                        "entity_gid": values.get("sentiment.entity_gid")[idx],
                        "entity_type": values.get("sentiment.entity_type")[idx],
                        "id": values.get("sentiment.id")[idx],
                        "id_type": values.get("sentiment.id_type")[idx],
                        "target_category": values.get("sentiment.target_category")[idx],
                        "target_type": values.get("sentiment.target_type")[idx],
                        "target_entity": values.get("sentiment.target_entity")[idx],
                    }
                )
                idx += 1
            values["sentiment"] = sentiment

        return values

    @classmethod
    def coalesce(cls, *args):
        for value in args:
            if value is not None:
                return value
        return ""

    @classmethod
    def from_ticket_dict(cls, ticket: dict, config: dict) -> "SemanticEvent":
        event_gid = uuid.uuid5(
            uuid.NAMESPACE_DNS,
            f'https://elko.is/support/ticket/{ticket.get("ticket_id")}/analysed',
        )
        event = SemanticEvent(
            **{
                "entity_gid": config.get("organization_gid"),
                "timestamp": ticket.get("updated_at"),
                "type": "track",
                "event": "Support Ticket Analysed",
                "event_gid": event_gid,
                "partition": config.get("partition"),
            }
        )
        analysis: dict = ticket.get("analysis", {})

        # content
        for ai_content in [
            {"field": "subject", "target": "anonymized_subject"},
            {"field": "executive_summary", "target": "summary"},
            {"field": "initial_response", "target": "customized_reply"},
            {"field": "urgency_reasoning", "target": "urgency_reasoning"},
            {"field": "priority_reasoning", "target": "priority_reasoning"},
            {
                "field": "completion_status_justification",
                "target": "completion_status_justification",
            },
        ]:
            if analysis.get(ai_content["field"]) is not None:
                txt_content = analysis.get(ai_content["field"], "")
                if not isinstance(txt_content, str):
                    txt_content = json.dumps(txt_content)
                event.content[ai_content["target"]] = txt_content

        for ai_dimension in [
            {"field": "inbound_outbound", "target": "inbound_outbound"},
            {"field": "urgency", "target": "urgency"},
            {"field": "priority", "target": "priority"},
        ]:
            if analysis.get(ai_dimension["field"]) is not None:
                event.dimensions[ai_dimension["target"]] = analysis.get(ai_dimension["field"])

        for ai_classification in [
            {"field": "urgency", "target": "urgency", "reasoning": "urgency_reasoning"},
            {"field": "priority", "target": "priority", "reasoning": "priority_reasoning"},
            {
                "field": "original_request_completion_status",
                "target": "completion_status",
                "reasoning": "completion_status_justification",
            },
        ]:
            if (
                analysis.get(ai_classification["field"]) is not None
                and analysis.get(ai_classification["target"]) is not None
            ):
                event.classification.append(
                    Classification(
                        type=ai_classification["target"],
                        value=analysis.get(ai_classification["field"]),
                        reasoning=analysis.get(f'{ai_classification["field"]}_reasoning', ""),
                    )
                )

        for tag in ticket.get("tags", []):
            event.classification.append(Classification(type="tag", value=tag))

        for ai_classification_lists in [
            {"field": "products", "target": "product"},
            {"field": "technology_and_brands", "target": "technology_and_brands"},
            {"field": "keywords", "target": "keyword"},
            {"field": "customer_tone_of_voice", "target": "customer_tone_of_voice"},
            {"field": "agent_tone_of_voice", "target": "agent_tone_of_voice"},
        ]:
            for item in analysis.get(ai_classification_lists["field"], []):
                if item is not None:
                    event.classification.append(
                        Classification(type=ai_classification_lists["target"], value=item)
                    )

        for intent in analysis.get("customer_intent", []):
            if intent is None:
                continue

            customer_intent = intent
            customer_intent_category = None
            if "  " in intent:
                customer_intent, customer_intent_category = intent.split("  ")

            event.classification.append(Classification(type="intent", value=customer_intent))
            if customer_intent_category is not None:
                event.classification.append(
                    Classification(type="intent_category", value=customer_intent_category)
                )

        for analysis_item in ticket.get("analysis_cost", []):
            event.analysis.append(Analysis(**analysis_item))

        for sentiment in analysis.get("entity_sentiment", []):
            if "reason" in sentiment:
                event.sentiment.append(
                    Sentiment(
                        type="Opinion",
                        sentiment=sentiment.get("sentiment"),
                        target_category=sentiment.get("target_category", sentiment.get("entity_type")),
                        target_type=sentiment.get("target_type", ""),
                        target_entity=sentiment.get("target_entity", sentiment.get("target_entity")),
                        entity=str(sentiment.get("entity", "")),
                        entity_id=str(sentiment.get("entity_id", "")),
                        reason=sentiment.get("reason", ""),
                    )
                )

        if ticket.get("ticket_id"):
            involvement = Involved(
                label="Ticket #" + str(ticket.get("ticket_id")) + " in Zendesk",
                role="Ticket",
                id=str(ticket.get("ticket_id")),
                id_type="Zendesk",
            )
            event.involves.append(involvement)

        for flag_field in ["incomplete", "spam", "relevant", "required_response"]:
            if analysis.get(flag_field) is not None:
                event.flags[flag_field] = analysis.get(flag_field)

        for flag in ticket.get("flags", []):
            event.flags[flag] = ticket.get(flag)

        return event


class SemanticEventCH(SemanticEvent):
    event_gid: uuid.UUID = Field(
        description="Event gid that must be set before saving the event. Calculate",
        default=uuid.UUID("00000000-0000-0000-0000-000000000000"),
    )

    @model_validator(mode="before")
    def pre_init(cls, values):
        return values

    @pydantic.field_serializer(
        "classification",
        "content",
        "type",
        "sentiment",
        "involves",
        "properties",
        "analysis",
        check_fields=False,
    )
    def my_field_serializer(self, value: Any, info: pydantic.FieldSerializationInfo) -> Any:
        if info.field_name == "classification":
            return {
                "classification.type": [c.type for c in value],
                "classification.value": [c.value for c in value],
                "classification.reasoning": [c.reasoning for c in value],
                "classification.score": [c.score for c in value],
                "classification.weight": [c.weight for c in value],
                "classification.confidence": [c.confidence for c in value],
            }
        elif info.field_name == "involves":
            return {
                "involves.label": [c.label for c in value],
                "involves.role": [c.role for c in value],
                "involves.entity_type": [c.entity_type for c in value],
                "involves.entity_gid": [c.entity_gid for c in value],
                "involves.id": [c.id for c in value],
                "involves.id_type": [c.id_type for c in value],
                "involves.capacity": [c.capacity for c in value],
            }
        elif info.field_name == "analysis":
            return {
                "analysis.item": [c.item for c in value],
                "analysis.provider": [c.provider for c in value],
                "analysis.variant": [c.variant for c in value],
                "analysis.token_in": [c.token_in for c in value],
                "analysis.token_out": [c.token_out for c in value],
                "analysis.amount": [c.amount for c in value],
                "analysis.processing_time": [c.processing_time for c in value],
                "analysis.currency": [c.currency for c in value],
            }
        elif info.field_name == "sentiment":
            return {
                "sentiment.type": [c.type for c in value],
                "sentiment.sentiment": [c.sentiment for c in value],
                "sentiment.reason": [c.reason for c in value],
                "sentiment.entity_gid": [c.entity_gid for c in value],
                "sentiment.entity_type": [c.entity_type for c in value],
                "sentiment.id": [c.id for c in value],
                "sentiment.id_type": [c.id_type for c in value],
                "sentiment.target_category": [c.target_category for c in value],
                "sentiment.target_type": [c.target_type for c in value],
                "sentiment.target_entity": [c.target_entity for c in value],
            }
        elif info.field_name == "type":
            return str(value.value)
        elif info.field_name == "properties":
            return_value = {}
            if value:
                for k, v in cast(dict, value).items():
                    if v is None:
                        continue
                    elif isinstance(v, (dict, list)):
                        return_value[k] = json.dumps(v)
                    else:
                        return_value[k] = str(v)
            return return_value
        elif info.field_name == "content":
            return {k: v for k, v in cast(dict, value).items() if v is not None}
