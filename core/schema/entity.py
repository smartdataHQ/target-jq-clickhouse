import re
import uuid
from datetime import UTC, datetime
from typing import Annotated, Any, Dict, Optional

import pydantic
from pydantic import BaseModel, Field, ValidationError, model_validator

from cxs.core.schema import CXSBase, OmitIfNone, empty_list
from cxs.core.schema.semantic_event import (
    Analysis,
    Involved,
    SemanticEvent,
    SemanticEventCH,
)
from cxs.core.utils.gid import create_gid, normalize_gid_url


class Content(CXSBase):
    label: str
    type: str
    sub_type: Annotated[Optional[str], OmitIfNone()] = Field(default="")
    value: Annotated[Optional[str], OmitIfNone()]
    language: Annotated[Optional[str], OmitIfNone()] = Field(default="")

    @model_validator(mode="before")
    def pre_init(cls, values):
        if "content_start" in values:
            values["content_starts"] = values["content_start"]
            del values["content_start"]
        return values


class Media(CXSBase):
    media_type: str = Field(default="")
    type: Annotated[Optional[str], OmitIfNone()]
    sub_type: Annotated[Optional[str], OmitIfNone()] = Field(default="")
    url: Annotated[Optional[str], OmitIfNone()]
    language: Annotated[Optional[str], OmitIfNone()] = Field(default="")
    aspect_ratio: Annotated[Optional[str], OmitIfNone()] = Field(default="")


class Embeddings(CXSBase):
    label: str
    model: str
    vectors: Annotated[Optional[list[float]], OmitIfNone()]
    content_starts: Annotated[Optional[str], OmitIfNone()] = Field(default="")
    content_ends: Annotated[Optional[str], OmitIfNone()] = Field(default="")
    opening_phrase: Annotated[Optional[str], OmitIfNone()] = Field(default="")
    closing_phrase: Annotated[Optional[str], OmitIfNone()] = Field(default="")


class ID(CXSBase):
    label: Annotated[Optional[str], OmitIfNone()]
    role: Annotated[Optional[str], OmitIfNone()]
    entity_type: Annotated[Optional[str], OmitIfNone()]
    entity_gid: Optional[uuid.UUID] = Field(
        uuid.UUID("00000000-0000-0000-0000-000000000000"),
        description="Event gid that must be set before saving the event. Calculate",
    )

    id: Annotated[Optional[str], OmitIfNone()] = Field(default="")
    id_type: Annotated[Optional[str], OmitIfNone()] = Field(default="")
    capacity: Annotated[Optional[float], OmitIfNone()] = Field(default=0)

    @model_validator(mode="before")
    def pre_init(cls, values):

        new_values = {}
        for key, value in values.items():
            # quickhand for pandas fields -> ids.<entity_type>.<role>.<id_type>.<label>
            if "." in key:
                keys = key.split(".")
                new_values["entity_type"] = keys[0]
                new_values["role"] = keys[1] if len(keys) > 1 else None
                new_values["id_type"] = keys[2] if len(keys) > 2 else None
                new_values["label"] = keys[3] if len(keys) > 3 else None
                new_values["id"] = value

        if new_values:
            values.update(new_values)

        if values.get("entity_gid") == "":
            values["entity_gid"] = None

        if values.get("id"):
            values["id"] = str(values["id"])

        if not values.get("label"):
            values["label"] = str(values["id"])

        return values


class Classification(CXSBase):
    type: Annotated[Optional[str], OmitIfNone()]
    value: Annotated[Optional[str], OmitIfNone()]
    babelnet_id: Annotated[Optional[str], OmitIfNone()] = Field(default="")
    weight: Annotated[Optional[float], OmitIfNone()] = Field(default=0)

    @model_validator(mode="before")
    def pre_init(cls, values):
        if "babel_id" in values:
            values["babelnet_id"] = values["babel_id"]
            del values["babel_id"]

        if "babelnet_id" not in values or not values["babelnet_id"]:
            values["babelnet_id"] = ""

        if "weight" not in values or not values["weight"]:
            values["weight"] = 0

        return values


class Location(CXSBase):
    type: Annotated[str, OmitIfNone()] = Field(description="Location type")
    label: Annotated[str, OmitIfNone()] = Field(description="Location label")
    country: Annotated[Optional[str], OmitIfNone()] = Field(description="Country name", default="")
    country_code: Annotated[Optional[str], OmitIfNone()] = Field(description="Country code", default="")
    code: Annotated[Optional[str], OmitIfNone()] = Field(description="Location code", default="")
    region: Annotated[Optional[str], OmitIfNone()] = Field(description="Region name", default="")
    division: Annotated[Optional[str], OmitIfNone()] = Field(description="Division name", default="")
    municipality: Annotated[Optional[str], OmitIfNone()] = Field(description="Municipality name", default="")
    locality: Annotated[Optional[str], OmitIfNone()] = Field(description="Locality name", default="")
    postal_code: Annotated[Optional[str], OmitIfNone()] = Field(description="Postal code", default="")
    postal_name: Annotated[Optional[str], OmitIfNone()] = Field(description="Postal name", default="")
    street: Annotated[Optional[str], OmitIfNone()] = Field(description="Street name", default="")
    street_nr: Annotated[Optional[str], OmitIfNone()] = Field(description="Street number", default="")
    address: Annotated[Optional[str], OmitIfNone()] = Field(description="Address", default="")

    longitude: Annotated[Optional[float], OmitIfNone()] = Field(description="Longitude", default=None)
    latitude: Annotated[Optional[float], OmitIfNone()] = Field(description="Latitude", default=None)
    geohash: Annotated[Optional[str], OmitIfNone()] = Field(description="Geohash", default=None)

    duration_from: Annotated[Optional[datetime], OmitIfNone()] = Field(
        description="Duration from", default=None
    )
    duration_until: Annotated[Optional[datetime], OmitIfNone()] = Field(
        description="Duration until", default=None
    )

    @model_validator(mode="before")
    def pre_init(cls, values):
        if not values.get("type"):
            values["type"] = "Location"

        if not values.get("label"):
            values["label"] = "Default"

        return values


class Entity(BaseModel):
    gid_url: str
    gid: uuid.UUID = Field(
        description="Event gid that must be set before saving the event. Calculate",
        default=uuid.UUID("00000000-0000-0000-0000-000000000000"),
    )

    label: str
    labels: Annotated[Optional[list[str]], OmitIfNone()] = Field(default=[])

    type: Annotated[Optional[str], OmitIfNone()] = Field(default="")
    variant: Annotated[Optional[str], OmitIfNone()] = Field(default="")
    icon: Annotated[Optional[str], OmitIfNone()] = Field(default="")
    colour: Annotated[Optional[str], OmitIfNone()] = Field(default="")

    dimensions: Annotated[Optional[Dict[str, str]], OmitIfNone()] = Field(default=dict())
    tags: Annotated[Optional[list[str]], OmitIfNone()] = Field(default=list())
    flags: Annotated[Optional[Dict[str, bool]], OmitIfNone()] = Field(default=dict())
    metrics: Annotated[Optional[Dict[str, float]], OmitIfNone()] = Field(default=dict())
    properties: Annotated[Optional[Dict[str, Any]], OmitIfNone()] = Field(default=dict())
    names: Annotated[Optional[Dict[str, str]], OmitIfNone()] = Field(default=dict())

    ids: Annotated[Optional[list[ID]], OmitIfNone()] = Field(default=list())
    content: Optional[list[Content]] = Field(default=list())
    media: Annotated[Optional[list[Media]], OmitIfNone()] = Field(default=list())
    embeddings: Annotated[Optional[list[Embeddings]], OmitIfNone()] = Field(default=list())
    classification: Optional[list[Classification]] = Field(default=list())
    location: Annotated[Optional[list[Location]], OmitIfNone()] = Field(default=list())
    agent_ids: Optional[list[uuid.UUID]] = Field(default=list())

    partition: str = Field(description="Partition of the event", default="_open_")
    sign: int = Field(description="Sign of the event", default=1)

    def get_content(self, labels: list[str]) -> str:
        return_string = ""
        for content in self.content:
            if content.label in labels:
                # remove everything that looks like images or links from markdown text using regex matching
                return_string += re.sub(r"!\[.*?\]\(.*?\)", "", content.value) + " \n"
        return re.sub(r"\n+", "\n", return_string) or "No content for the specified label(s)"

    def get_all_content(self, exclude_types: list[str] = []) -> list[str]:
        """
        Parsed documents have labels like '218_4001', '4002_5967' which are character ranges
        in the parsed text, and not names like "content", "summary" as the `get_content` method
        expects.

        Args:
            exclude_types (list[str]): types to exclude f.ex "summary".

        Returns:
            list of content strings.
        """
        if not self.content:
            return []

        return [
            content.value
            for content in self.content
            if content.type not in exclude_types and content.value is not None
        ]

    @model_validator(mode="before")
    def pre_init(cls, values):
        if isinstance(values, Entity):
            values = dict(values)

        if "_type" in values and values["_type"] == "clickhouse":
            return cls.from_clickhouse(values)

        if not values.get("partition"):
            values["partition"] = "_open_"

        if values.get("gid_url"):
            values["gid_url"] = normalize_gid_url(values["gid_url"])
            if not values.get("gid"):
                values["gid"] = create_gid(values["gid_url"])

        values["classification"] = [
            cf
            for cf in values.get("classification", [])
            if isinstance(values.get("classification", [])[0], Classification) or cf.get("value") is not None
        ]

        # loop over all fields in values and reassign values if the have '.' in them
        groups = {}
        for key, value in values.items():
            if "." in key:
                keys = key.split(".")
                if keys[0] not in groups:
                    groups[keys[0]] = {}
                if value:
                    groups[keys[0]][".".join(keys[1:])] = value

        for key, value in groups.items():
            if key in ["ids"] and isinstance(value, dict):
                values[key] = [ID(**{key: value}) for key, value in value.items()]
            elif key == "labels":
                if not values.get(key):
                    values[key] = []
                values[key].append(list(value.values())[0])
            elif key == "location":
                values[key] = [Location(**value)]
            else:
                values[key] = value

        return values

    @classmethod
    def from_clickhouse(cls, values):

        if values.get("embeddings.label") is not None:
            embeddings = []
            idx = 0
            for some in values.get("embeddings.label"):
                embeddings.append(
                    {
                        "label": values.get("embeddings.label")[idx],
                        "model": values.get("embeddings.model")[idx],
                        "vectors": values.get("embeddings.vectors")[idx],
                        "content_starts": values.get("embeddings.content_starts")[idx],
                        "content_ends": values.get("embeddings.content_ends")[idx],
                        "opening_phrase": values.get("embeddings.opening_phrase")[idx],
                        "closing_phrase": values.get("embeddings.closing_phrase")[idx],
                    }
                )
                idx += 1
            values["embeddings"] = embeddings

        if values.get("ids.label") is not None:
            ids = []
            idx = 0
            for some in values.get("ids.label"):
                ids.append(
                    {
                        "label": values.get("ids.label")[idx],
                        "role": values.get("ids.role")[idx],
                        "entity_type": values.get("ids.entity_type")[idx],
                        "entity_gid": values.get("ids.entity_gid")[idx],
                        "id": values.get("ids.id")[idx],
                        "id_type": values.get("ids.id_type")[idx],
                        "capacity": values.get("ids.capacity")[idx],
                    }
                )
                idx += 1
            values["ids"] = ids

        if values.get("media.type") is not None:
            media = []
            idx = 0
            for some in values.get("media.type"):
                media.append(
                    {
                        "media_type": values.get("media.media_type")[idx],
                        "type": values.get("media.type")[idx],
                        "sub_type": values.get("media.sub_type")[idx],
                        "url": values.get("media.url")[idx],
                        "language": values.get("media.language")[idx],
                        "aspect_ratio": values.get("media.aspect_ratio")[idx],
                    }
                )
                idx += 1
            values["media"] = media

        if values.get("location.type") is not None:
            locations = []
            idx = 0
            for some in values.get("location.type"):
                locations.append(
                    {
                        "type": values.get("location.type")[idx],
                        "label": values.get("location.label")[idx],
                        "country": values.get("location.country")[idx],
                        "country_code": values.get("location.country_code")[idx],
                        "code": values.get("location.code")[idx],
                        "region": values.get("location.region")[idx],
                        "division": values.get("location.division")[idx],
                        "municipality": values.get("location.municipality")[idx],
                        "locality": values.get("location.locality")[idx],
                        "postal_code": values.get("location.postal_code")[idx],
                        "postal_name": values.get("location.postal_name")[idx],
                        "street": values.get("location.street")[idx],
                        "street_nr": values.get("location.street_nr")[idx],
                        "address": values.get("location.address")[idx],
                        "longitude": values.get("location.longitude")[idx],
                        "latitude": values.get("location.latitude")[idx],
                        "geohash": values.get("location.geohash")[idx],
                    }
                )
                idx += 1
            values["location"] = locations

        if values.get("content.type") is not None:
            contents = []
            idx = 0
            for some in values.get("content.type"):
                contents.append(
                    {
                        "label": values.get("content.label")[idx],
                        "type": values.get("content.type")[idx],
                        "sub_type": values.get("content.sub_type")[idx],
                        "value": values.get("content.value")[idx],
                        "language": values.get("content.language")[idx],
                    }
                )
                idx += 1
            values["content"] = contents

        if values.get("classification.type") is not None:
            classifications = []
            idx = 0
            for some in values.get("classification.type"):
                classifications.append(
                    {
                        "type": values.get("classification.type")[idx],
                        "value": values.get("classification.value")[idx],
                        "babelnet_id": values.get("classification.babelnet_id")[idx],
                        "weight": values.get("classification.weight")[idx],
                    }
                )
                idx += 1
            values["classification"] = classifications

        return values

    @classmethod
    def coalesce(cls, *args):
        for value in args:
            if value is not None:
                return value
        return ""


class EntityCH(Entity):

    @pydantic.field_serializer(
        "classification",
        "content",
        "ids",
        "embeddings",
        "media",
        "location",
        "dimensions",
        "flags",
        "metrics",
        "properties",
        "names",
        check_fields=False,
    )
    def my_ch_serializer(self, value: Any, info: pydantic.FieldSerializationInfo) -> Any:
        default_gid = uuid.UUID("00000000-0000-0000-0000-000000000000")
        if info.field_name == "classification":
            return {
                "classification.type": [c.type for c in value],
                "classification.value": [c.value for c in value],
                "classification.babelnet_id": [c.babelnet_id for c in value],
                "classification.weight": [c.weight for c in value],
            }
        elif info.field_name == "ids":
            id = {
                "ids.label": [c.label for c in value],
                "ids.role": [c.role for c in value],
                "ids.entity_type": [c.entity_type for c in value],
                "ids.entity_gid": [c.entity_gid or default_gid for c in value],
                "ids.id": [c.id for c in value],
                "ids.id_type": [c.id_type for c in value],
                "ids.capacity": [c.capacity or 0 for c in value],
            }
            return id

        elif info.field_name == "embeddings":
            return {
                "embeddings.label": [c.label for c in value],
                "embeddings.content_starts": [c.content_starts for c in value],
                "embeddings.content_ends": [c.content_ends for c in value],
                "embeddings.opening_phrase": [c.opening_phrase for c in value],
                "embeddings.closing_phrase": [c.closing_phrase for c in value],
                "embeddings.vectors": [c.vectors for c in value],
                "embeddings.model": [c.model for c in value],
            }

        elif info.field_name == "media":
            return {
                "media.media_type": [c.media_type for c in value],
                "media.type": [c.type for c in value],
                "media.sub_type": [c.sub_type or "" for c in value],
                "media.url": [c.url for c in value],
                "media.language": [c.language or "" for c in value],
                "media.aspect_ratio": [c.aspect_ratio or "" for c in value],
            }

        elif info.field_name == "content":
            return {
                "content.label": [c.label for c in value],
                "content.type": [c.type for c in value],
                "content.sub_type": [c.sub_type or "" for c in value],
                "content.value": [c.value for c in value],
                "content.language": [c.language or "" for c in value],
            }

        elif info.field_name == "location":
            return {
                "location.type": [c.type for c in value],
                "location.label": [c.label for c in value],
                "location.country": [c.country for c in value],
                "location.country_code": [c.country_code for c in value],
                "location.code": [c.code for c in value],
                "location.region": [c.region for c in value],
                "location.division": [c.division for c in value],
                "location.municipality": [c.municipality for c in value],
                "location.locality": [c.locality for c in value],
                "location.postal_code": [c.postal_code for c in value],
                "location.postal_name": [c.postal_name for c in value],
                "location.street": [c.street for c in value],
                "location.street_nr": [c.street_nr for c in value],
                "location.address": [c.address for c in value],
                "location.longitude": [c.longitude for c in value],
                "location.latitude": [c.latitude for c in value],
                "location.geohash": [c.geohash for c in value],
                "location.duration_from": [c.duration_from for c in value],
                "location.duration_until": [c.duration_until for c in value],
            }

        elif info.field_name == "type":
            return str(value.value)
        elif info.field_name == "dimensions":
            return {k: v for k, v in value.items() if v is not None}
        elif info.field_name == "properties":
            return {k: v for k, v in value.items() if v is not None}
        elif info.field_name == "metrics":
            return {k: v for k, v in value.items() if v is not None}
        elif info.field_name == "names":
            return {k: v for k, v in value.items() if v is not None}
        elif info.field_name == "flags":
            return {k: v for k, v in value.items() if v is not None}


class EntitySolr(Entity):

    def to_stacked_solr(self) -> [dict]:
        entities = []
        for idx, embedding in enumerate(self.embeddings):

            if not embedding.vectors:
                continue

            entity = {
                "id": str(self.gid) + "-" + str(idx) if len(self.embeddings) > 1 else str(self.gid),
                "gid": str(self.gid),
                "gid_url": self.gid_url,
                "type": self.type,
                "variant": self.variant,
                "label": self.label,
                "labels": self.labels,
                "tags": self.tags,
                "partition": self.partition,
                "ids": list(set([c.id for c in self.ids])),
                "category_l1": "".join([c.value for c in self.classification if c.type == "CategoryL1"]),
                "category_l2": "".join([c.value for c in self.classification if c.type == "CategoryL2"]),
                "category_l3": "".join([c.value for c in self.classification if c.type == "CategoryL3"]),
                "category_l4": "".join([c.value for c in self.classification if c.type == "CategoryL4"]),
                "brand": self.dimensions.get("brand", ""),
                "product_line": self.dimensions.get("product_line", ""),
                "product_variant": self.dimensions.get("product_variant", ""),
                "product": self.dimensions.get("product", ""),
                "model": self.dimensions.get("model", ""),
                "embeddings": embedding.vectors,
                "content": (
                    "\n".join(
                        piece.value.replace("\n", "</br></br>")
                        for piece in self.content
                        if piece.type not in ["q_and_a", "search_words"]
                    )
                    if embedding.label == "_various"
                    else self.content[0].value
                ),
            }
            """
              <field name="search_words" type="string" multiValued="true" indexed="true" stored="true"/>
              <field name="price" type="pfloat" multiValued="false" indexed="true" stored="true"/>
              <field name="color" type="pfloat" multiValued="false" indexed="true" stored="true"/>
              <field name="availability" type="string" multiValued="false" indexed="true" stored="true"/>

              <dynamicField indexed="true" multiValued="false" name="metric_*" type="pfloat" stored="true"/>
              <dynamicField indexed="true" multiValued="false" name="dim_*" type="string" stored="true"/>
              <dynamicField indexed="true" multiValued="false" name="flag_*" type="boolean" stored="true"/>
              <dynamicField indexed="true" multiValued="false" name="spec_*" type="string" stored="true"/>
              <dynamicField indexed="true" multiValued="false" name="loc_*" type="location" stored="true"/>
            """
            entities.append(entity)
        return entities


class CostTrackingEntity(Entity):
    """
    An updated Entity that stores analysis information for allowing cost tracking information
    to flow through the system. Copied from a similar concept on the SemanticEvent class, which
    is the class that ends up being serialised to the database to persist the cost information.

    Also used to track the actual event of "a new document was analysed" regardless of the existence
    of any cost analysis information; the .to_semantic_event() method creates a SemanticEvent instance
    that is derived from the entity data representing the 'analysis event'.
    """

    analysis: Annotated[Optional[list[Analysis]], OmitIfNone()] = Field(
        description="Flags of the event",
        default_factory=lambda: empty_list(),
    )

    @staticmethod
    def from_entity(entity: Entity) -> "CostTrackingEntity":
        return CostTrackingEntity.model_validate(entity)

    def to_entity_ch(self) -> EntityCH:
        """
        Cast to the EntityCH for inserting to Clickhouse

        NOTE: we use `dict(self)` here deliberately because the OmitIfNone logic prevents
        us from correctly recreating the Embeddings instances (it removes the empty vectors list).
        """
        return EntityCH(**dict(self))

    def to_semantic_event(self) -> SemanticEvent:
        """Cast to a SemanticEvent instance"""
        timestamp = datetime.now(UTC).isoformat()
        _type = "track"
        event = "Document Analysed"
        event_gid_url = f"https://{self.partition}/event/{_type}/{event.replace(' ', '-')}/{timestamp}"
        event_gid = uuid.uuid5(uuid.NAMESPACE_DNS, event_gid_url.lower())

        return SemanticEvent(
            entity_gid=self.gid,
            timestamp=timestamp,
            type=_type,
            event=event,
            event_gid=event_gid,
            dimensions=self.dimensions,
            properties=self.properties,
            metrics=self.metrics,
            flags=self.flags,
            analysis=self.analysis,
            involves=[
                Involved(
                    label=self.label,
                    role="Document",
                    entity_type="Document",
                    entity_gid=self.gid,
                    id=self.gid_url,
                    id_type="URL",
                )
            ],
            partition=self.partition,
            sign=self.sign,
        )

    def to_semantic_event_ch(self) -> SemanticEventCH:
        """Cast to a SemanticEventCH instance for inserting to Clickhouse"""
        return SemanticEventCH(**self.to_semantic_event().model_dump())
