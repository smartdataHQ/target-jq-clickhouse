import uuid
import pandas as pd
import slugify
import math

from datetime import datetime
from enum import Enum
from typing import Dict, Any
from typing import Optional
from pydantic import BaseModel, Field, model_validator, field_serializer, FieldSerializationInfo
from cxs.core.schema.entity import Entity, Location
from cxs.core.schema.uom import UOM
from cxs.core.utils.gid import create_gid

class ValueType(str, Enum):
    Actual = 'Actual'               # This value represents an actual value
    Goal = 'Goal'                   # This value represents a goal
    Estimation = 'Estimation'       # This value represents an estimation
    Projection = 'Projection'       # This value represents a projection
    Forecast = 'Forecast'           # This value represents a forecast
    Official = 'Official'           # This value represents an official
    Unknown = 'Unknown'             # This value of unknown type

class DefaultAgg(str, Enum):
    Sum = 'Sum'                     # Sum of the values is the default aggregation
    Avg = 'Avg'                     # Average of the values is the default aggregation
    Min = 'Min'                     # Minimum of the values is the default aggregation
    Max = 'Max'                     # Maximum of the values is the default aggregation
    Custom = 'Custom'               # Custom aggregation is the default aggregation

class TMAmountAdj(str, Enum):
    NotAdjusted = 'NotAdjusted'     # This monetary amount is not adjusted
    Adjusted = 'Adjusted'           # This monetary amount is adjusted on a specific date
    Obfuscated = 'Obfuscated'       # This monetary amount is obfuscated or somehow distorted
    Unknown = 'Unknown'             # This monetary amount is of unknown adjustment type

class TSType(str, Enum):
    SingleMetric = 'SingleMetric'   # This timeseries only has one metric
    MultiMetrics = 'MultiMetrics'   # this is a multi-metric timeseries

# `access_type` Enum8('Local' = 0, 'Exclusive' = 1, 'Group' = 2, 'SharedPercentiles' = 3, 'SharedObfuscated' = 4, 'Shared' = 5, 'Public' = 6) DEFAULT(1),
class TSAccess(str, Enum):
    Local = 'Local'                         # Private to the customer that owns the data
    Exclusive = 'Exclusive'                 # Exclusively offered to specific customers
    Group = 'Group'                         # Shared with a group of customers
    SharedPercentiles = 'SharedPercentiles' # Shared with all customers with percentiles (Somewhat Obfuscated)
    SharedObfuscated = 'SharedObfuscated'   # Shared with all customers with obfuscated values
    Shared = 'Shared'                       # Shared with all customers
    Public = 'Public'                       # Publicly available

class TSCompleteness(str, Enum):
    Unspecified = 'Unspecified' # The completeness of the data is unspecified
    Partial = 'Partial'     # The data is partially complete
    InProgress = 'InProgress'   # The data is in progress
    Complete = 'Complete'    # The data is complete
    Verified = 'Verified'    # The data is verified
    Golden = 'Golden'      # The data is golden
    Unknown = 'Unknown'      # The data is of unknown completeness
    Irrelevant = 'Irrelevant'   # The data completeness is irrelevant

class TSResolution(str, Enum):
    PNT = 'PNT'
    P1Y = 'P1Y'
    P1Q = 'P1Q'
    P2M = 'P2M'
    P1M = 'P1M'
    P2W = 'P2W'
    P1W = 'P1W'
    P1D = 'P1D'
    PT1H = 'PT1H'
    PT30M = 'PT30M'
    PT15M = 'PT15M'
    PT10M = 'PT10M'
    PT5M = 'PT5M'
    PTM = 'PT1M'
    PT1S = 'PT1S'

class TSCategory(str, Enum):
    Agriculture = 'Agriculture'
    Communication = 'Communication'
    Culture = 'Culture'
    Demography = 'Demography'
    Economy = 'Economy'
    Education = 'Education'
    Energy = 'Energy'
    Environment = 'Environment'
    Geography = 'Geography'
    Governance = 'Governance'
    Health = 'Health'
    Industry = 'Industry'
    Infrastructure = 'Infrastructure'
    Media = 'Media'
    Other = 'Other'
    Philosophy = 'Philosophy'
    Politics = 'Politics'
    Physics = 'Physics'
    Religion = 'Religion'
    Science = 'Science'
    Security = 'Security'
    Society = 'Society'
    SocialMedia = 'SocialMedia'
    Sports = 'Sports'
    Technology = 'Technology'
    Tourism = 'Tourism'
    Transportation = 'Transportation'
    Weather = 'Weather'

class DefinedMetric(BaseModel):
    gid_url: str # RDF URL for the time series
    gid: uuid.UUID = Field(description="Event gid that must be set before saving the event. Calculate")

    category: str # The category of the metric
    label: str # The full name of the metric
    slug: str  # The slug of the metric as used in metrics{'slug': value}

    # all values are stored using this format, scaled values is not allowed
    uom: UOM = Field(..., description='The unit of measure for the metric') #Removed: , max_digits=4 - not applicable to string value

    currency: Optional[str] = Field(description='The currency of the metric', default='') # The currency of the metric
    adj_type: Optional[TMAmountAdj] = Field(description= 'Adjustment type for the metric', default=TMAmountAdj.NotAdjusted) # The adjustment type for the metric
    adj_date: Optional[str] = Field(description='Date of adjustment', default='')

    wid: Optional[str] = Field(..., description='WikiData ID for what is being measured. Q15645384 -> https://www.wikidata.org/wiki/Q15645384')
    concept_id: Optional[str] = Field(..., description='Concept ID for what is being measured. wheat -> https://conceptnet.io/c/en/wheat')
    synset_id: Optional[str] = Field(..., description='Concept ID for what is being measured. bn:00080959n -> https://babelnet.org/synset?id=bn:00080959n&orig=wheat')

    agg: DefaultAgg = Field(description='Default aggregation type for the metric', default=DefaultAgg.Sum) # The default aggregation type for the metric

    @model_validator(mode="before")
    def pre_init(cls, values):
        assert values.get("category") is not None, "Category must be set"
        assert values.get("label") is not None, "Label must be set"
        assert values.get("uom") is not None, "Unit of measure must be set"

        values["gid_url"] = f"https://quicklookup.com/metrics/{conform_label(values.get('category'))}/{conform_label(values.get('label'))}/{values.get('uom').name[5:]}"

        # slug is always calculated from the label and the uom
        values["slug"] = slugify.slugify(values["label"],separator='_') + '_' + slugify.slugify(values["uom"].name[5:])
        if values.get("currency"):
            values["currency"] = values.get("currency").lower()
            values["slug"] = values["slug"] + '_' + values["currency"]
            values["gid_url"] = values["gid_url"] + '/' + values["currency"].upper()

        if values.get("adj_type") or values.get("adj_date"):
            if values.get("adj_type") == TMAmountAdj.Adjusted:
                assert values.get("adj_date") is not None, "Adjustment data must be set when currency is adjusted"

        values["gid"] = create_gid(values.get("gid_url"), normalize=True)

        return values

class DPEntity(BaseModel):
    label: str
    type: str
    gid: uuid.UUID = Field(
        description="Event gid that must be set before saving the event. Calculate",
        default=uuid.UUID("00000000-0000-0000-0000-000000000000"),
    )
    gid_url: str

class DataPoint(BaseModel):

    entity_gid: Optional[str] = Field(description='The entity of the data point', default=None) # the entity of the data point
    entity_gid_url: Optional[str] = Field(description='The entity of the data point', default=None) # the entity of the data point

    measured_by_gid: Optional[str] = Field(description='The gid of the entity that measured the data point', default=None) # the entity of the data point
    measured_by_gid_url: Optional[str] = Field(description='The gid_url of the entity that measured the data point', default=None) # the entity of the data point

    timestamp: datetime # the timestamp of the data point

    dimensions: Optional[Dict[str, str]] = Field(description='Dimensions dictionary for this datapoint', default=dict()) # the dimensions of the data point
    metrics: Dict[str, float] = Field(description='Metrics dictionary for this datapoint')

    location: Optional[Location] = Field(description='The location of the data point', default=None) # the location of the data point
    demography: Optional[Dict[str, str]] = Field(description='The demography metadata for this data point', default=dict()) # the location of the data point
    classification: Optional[Dict[str, str]] = Field(description='Classification metadata for this datapoint', default=dict()) # the classification of the data point
    topology: Optional[Dict[str, str]] = Field(description='Topology metadata for this datapoint', default=dict()) # the topology of the data point
    usage: Optional[Dict[str, str]] = Field(description='Usage metadata for this datapoint', default=dict()) # the usage of the data point
    device: Optional[Dict[str, str]] = Field(description='Device metadata for this datapoint', default=dict()) # the device of the data point
    product: Optional[Dict[str, str]] = Field(description='Product metadata for this datapoint', default=dict()) # the device of the data point

    flags: Optional[Dict[str, bool]] = Field(description='Flags metadata for this datapoint', default=dict()) # the flags of the data point
    tags: Optional[list[str]] = Field(description='Tags metadata for this datapoint', default=list()) # the tags of the data point

    # Stop using this and favor a timeseries based metadata
    # mtype: Optional[Dict[str, str]] = Field(description='Measurement type metadata for this datapoint', default=dict()) # the measurement type of the data point
    # uom: Optional[Dict[str, str]] = Field(description='Unit of measure metadata for this datapoint', default=dict()) # the unit of measure of the data point
    # of_what: Optional[Dict[str, str]] = Field(description='What is being measured metadata for this datapoint', default=dict()) # the what is being measured of the data point

    access_type: Optional[TSAccess] = Field(description='Access type for the data point', default=TSAccess.Public) # The access type for the data point
    signature: Optional[uuid.UUID] = Field(description="Used to discriminate between different versions of the same data point", default=None)

    @model_validator(mode="before")
    def pre_init(cls, values):
        new_structure = {}
        for key, value in values.items():
            if '.' in key:
                type, item = key.split('.')
                if type in ['metrics']:
                    if not new_structure.get(type):
                        new_structure[type] = {}
                    if not math.isnan(value):
                        new_structure[type][item] = value
        values.update(new_structure)
        return values

class TimeSeries(BaseModel):
    # For external datasets we use URL: https://thedocs.worldbank.org/en/doc/7d852628d96b9411d43e5d36d5dff941-0050062022/original/Graphs-Chapter-5-02082022.xlsx
    # For interna datasets we use our URL: https://quicklookup/timeseries/Energy/Prices
    # Specific Timeseries or generic, both are good (External are usually specific)
    # For internal datasets we use our URL: https://quicklookup/timeseries/Energy/Prices/<publisher>/<publication>/<series_type>/<slug>
    # With multiple metrics URL: https://quicklookup/timeseries/Energy/Prices/<publisher>/<publication>/<series_type>/<slug>/<metric_slug_1>
    # With multiple metrics URL: https://quicklookup/timeseries/Energy/Prices/<publisher>/<publication>/<series_type>/<slug>/<metric_slug_2>
    # With multiple metrics URL: https://quicklookup/timeseries/Energy/Prices/<publisher>/<publication>/<series_type>/<slug>/<metric_slug_2>

    gid_url: str # RDF URL for the time series
    gid: uuid.UUID = Field(description="Event gid that must be set before saving the event. Calculate")

    group_gid_url: str # RDF URL for the time series
    group_gid: Optional[uuid.UUID] = Field(description="Event gid that must be set before saving the event. Calculate", default=None)

    label: str
    slug: str
    value_types: ValueType = Field(description='The value type of the time series', default=ValueType.Actual) # The value type of the time series
    completeness: TSCompleteness = Field(description='The completeness of the time series', default=TSCompleteness.Complete) # The completeness of the time series

    category: TSCategory
    sub_category: Optional[str]

    resolution: TSResolution
    metrics: Dict[str, DefinedMetric] # str = slug
    datapoints: list[DataPoint] = Field(description='The data points of the time series', default=list()) # str = timestamp

    owner: Optional[Entity]
    source: Entity
    publisher: Optional[Entity]
    publication: Optional[Entity] = Field(description='The publication of the time series', default=None) # The publication of the time series
    series_type: Optional[TSType] = Field(description='Type of time series', default=TSType.MultiMetrics) # The type of time series

    entities: Optional[list[Entity]] = Field(description='Type of time series', default=list())

    access: TSAccess = Field(description='Access type for the time series', default=TSAccess.Public) # The access type for the time series
    country: str = Field(description='Country Code is the partition for the time series', default='_open_') # The partition for the time series

    def add_datapoints(self, df: pd.DataFrame):
        self.datapoints += [DataPoint(**item) for item in df.to_dict(orient='records')]

    def as_entity(self):
        return Entity(**self.model_dump(exclude={'gid', 'gid_url', 'group_gid', 'group_url', 'datapoints', 'metrics', 'entities'}))

    # Automatic validation at initialization of the TimeSeries class
    @model_validator(mode="before")
    def pre_init(cls, values):

        if not values.get("category"):
            raise ValueError("Category must be set")
        if not values.get("sub_category"):
            raise ValueError("Sub category must be set")
        if not values.get("label"):
            raise ValueError("Label must be set")
        if not values.get("resolution"):
            raise ValueError("Resolution must be set")
        if not values.get("owner"):
            raise ValueError("Owner must be set")
        if not values.get("metrics"):
            raise ValueError("Metrics must be set")
        if not values.get("country"):
            raise ValueError("Country must be set")

        values["slug"] = slugify.slugify(values["label"], separator='_')

        if not values.get("value_types"):
            values["value_types"] = ValueType.Actual

        if not values.get("completeness"):
            values["completeness"] = TSCompleteness.Complete

        if not values.get("data_points"):
            values["data_points"] = []

        if not values.get("publisher") and values.get("owner"):
            values["publisher"] = values.get("owner")

        if not values.get("source") and values.get("owner"):
            values["source"] = values.get("owner")

        if not values.get("gid_url"):
            # For internal datasets we use our URL: https://quicklookup.com/timeseries/Energy/Prices/<series_type>/<slug>
            values["gid_url"] = f"https://quicklookup.com/timeseries/{values.get('category').name}/{values.get('sub_category')}/{conform_label(values.get('label'))}/{values.get('value_types').name}/{values.get('resolution').name}"

        values["gid"] = create_gid(values.get("gid_url"), normalize=True)
        values["group_gid_url"] = f"https://quicklookup.com/timeseries/{values.get('category').name}/{values.get('sub_category')}/{conform_label(values.get('label'))}"
        values["group_gid"] = create_gid(values.get("group_gid_url"), normalize=True)

        return values

    @model_validator(mode='after')
    def post_init(self):
        if len(self.country.strip()) != 3:
            raise ValueError(f"Country Code '{self.country}' is not a valid 3-character country code.")

class TimeSeriesCH(TimeSeries):

    @field_serializer("metrics","value_types", "resolution", "completeness", "access", "category", check_fields=False)
    def my_ch_serializer(self, value: Any, info: FieldSerializationInfo) -> Any:
        if info.field_name == "metrics":
            fields = ["gid_url", "gid", "category", "label", "slug", "uom", "currency", "adj_type", "adj_date", "wid", "concept_id", "synset_id", "agg"]
            items = {}
            for field in fields:
                items['metrics.'+field] = []
            for key, value in value.items():
                if isinstance(value, DefinedMetric):
                    for field in fields:
                        items['metrics.'+field].append(str(getattr(value, field)))
            return items
        else:
            if isinstance(value, Enum):
                return value.name
            else:
                return value

def conform_label(label: str) -> str:
    new_label = label.strip()
    new_label = new_label.title()
    new_label = new_label.replace("_", " ")
    new_label = new_label.replace("-", " ")
    new_label = new_label.replace(" ", "")
    return new_label