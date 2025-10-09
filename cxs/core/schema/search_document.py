import datetime
import uuid
from enum import Enum
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field, model_validator

from cxs.core.schema import OmitIfNone
from cxs.core.schema.entity import Classification, ID, Media
from cxs.core.schema.search import SearchBase, SearchDocumentMeta, SearchResultsMeta


class DocumentImage(BaseModel):
    uri: str
    width: int
    height: int


class DocumentRelevance(Enum):
    complete = "complete"
    partial = "partial"
    some = "some"
    slight = "slight"
    no = "no"


class DocumentCompleteness(Enum):
    all = "all"
    some = "some"
    none = "none"


class DocumentOnTopic(Enum):
    completely = "directly"
    mostly = "mostly"
    slightly = "slightly"
    adjacent = "adjacent"
    mostly_off = "mostly_off"
    off_topic = "off"


class DocumentAge(Enum):
    new = "new"
    recent = "recent"
    dated = "dated"
    old = "old"


class Embedding(BaseModel):
    text: str
    vector: list[float]
    images: list[DocumentImage]


class LLMCost(BaseModel):
    item: Optional[str] = Field(None, description="The item that the cost is for.")
    provider: Optional[str] = Field(None, description="The provider that the cost is for.")
    model: Optional[str] = Field(None, description="The model used for analysis.")
    variant: Optional[str] = Field(None, description="The model-variant used for analysis.")
    processing_time: Optional[int] = Field(None, description="The processing time that the analysis took.")
    token_in: Optional[int] = Field(None, description="The number of tokens in.")
    token_out: Optional[int] = Field(None, description="The number of tokens out.")
    temperature: Optional[float] = Field(None, description="The temperature for analysis.")
    currency: Optional[str] = Field(None, description="The currency for the cost.")
    amount: Optional[float] = Field(None, description="The amount for the cost.")


class DocumentReranking(SearchBase):
    # summary: Annotated[Optional[str], OmitIfNone()] = Field(
    #    ...,
    #    description="Direct copy of the document parts that are useful when answering the questions. Only contains text found in the document. This must not be the answer or an attempt to provide an answer, just all relevant content, condensed and copied over. Do not translate the content or alter it in any way.",
    # )
    id: str = Field(..., description="The document ID")
    on_topic_rank: int = Field(
        ...,
        description="Is this content directly on topic to answer the question? This ranges from 10 to 0",
    )
    requires_full: int = Field(
        ...,
        description="10 indicates that the summary is enough to answer the question. 0 indicates that the document as a whole may be needed.",
    )
    requirements_rank: int = Field(
        ...,
        description="Does the product meet all or some requirements indicated in the question? This ranges from 10 to 0",
    )
    score: int = Field(..., description="How good is the document for the question? This ranges from 10 to 0")
    age: DocumentAge = Field(
        ...,
        description="How recent is the information in the document. This is a subjective measure of the information in the document and the context of the question asked.",
    )
    id: int = Field(..., description="Document ID")
    # cost: Optional[dict] = Field(..., description='Ignore this field completely')


class DocumentsReranking(SearchBase):
    documents: list[DocumentReranking] = Field(..., description="The documents to rerank.")


class EntityContent(SearchBase):

    label: str = Field(..., description="The label/title for the entity.")
    type: str = Field(..., description="The type of the entity.")
    sub_type: str = Field(..., description="The type of the entity.")
    value: str = Field(..., description="The value of the entity.")
    language: str = Field(description="The language of the entity.", default="en")
    meta_description: str = Field(description="The meta description of the entity.", default="")
    dist: float = Field(description="The distance metric if this is a part of source.", default=0.0)

    @model_validator(mode="before")
    def pre_init(cls, values):
        if isinstance(values, list):
            values = values[0]
        return values


class MinimalDocument(SearchBase):
    gid: uuid.UUID = Field(None, description="Document gid.")
    gid_url: str = Field(None, description="Document gid_url.")
    label: Annotated[Optional[str], OmitIfNone()] = Field("", description="label/title for the document.")
    last_updated: Optional[datetime.datetime] = Field(None, description="Document last updated.")
    content: Annotated[Optional[str], OmitIfNone()] = Field(
        "", description="The content of the document that the vector matched."
    )
    keywords: Annotated[Optional[list[str]], OmitIfNone()] = Field(
        None, description="The keywords set on the document."
    )
    dimensions: Annotated[Optional[dict[str, Any]], OmitIfNone()] = Field(
        None, description="The dimensions set on the document."
    )

    @model_validator(mode="before")
    def pre_init(cls, values):

        if issubclass(values.__class__, BaseModel):
            values = values.model_dump()

        if isinstance(values.get("content", None), str):
            main_content = [values["content"]]
        else:
            main_content = [
                c["value"]
                for c in values.get("content", [])
                if c["label"] == "content" or c["sub_type"] == "chunk"
            ]
        values["keywords"] = [c["value"] for c in values.get("classification", []) if c["type"] == "keyword"]
        values["content"] = "\n".join(main_content) if main_content and len(main_content) > 0 else ""
        return values


class DocumentListItem(SearchBase):
    gid: uuid.UUID = Field(None, description="Document gid.")
    gid_url: str = Field(None, description="Document gid_url.")
    label: Annotated[Optional[str], OmitIfNone()] = Field("", description="label/title for the document.")
    type: Annotated[Optional[str], OmitIfNone()] = Field(None, description="The type of the document.")
    variant: Annotated[Optional[str], OmitIfNone()] = Field("", description="The variant of the document.")
    embeddings_model: Annotated[Optional[list[str]], OmitIfNone()] = Field(
        None, description="The embedding model used to create vectors for this document."
    )
    last_updated: Annotated[Optional[datetime.datetime], OmitIfNone()] = Field(
        None, description="Document last updated."
    )
    updated: Annotated[Optional[datetime.datetime], OmitIfNone()] = Field(
        None, description="Document last synced."
    )
    state: Annotated[Optional[str], OmitIfNone()] = Field(None, description="State of the document")
    usable_by_agent: Annotated[Optional[bool], OmitIfNone()] = Field(
        None,
        description="Whether the agent can use the document",
    )
    private_document: Annotated[Optional[bool], OmitIfNone()] = Field(
        None,
        description="Whether the document was marked as private",
    )

    @model_validator(mode="before")
    def pre_init(cls, values):

        if issubclass(values.__class__, BaseModel):
            values = values.model_dump()

        if "updated" in values and not values.get("updated", None):
            del values["updated"]

        if "embeddings.model" in values:
            values["embeddings_model"] = list(set(values["embeddings.model"]))
            del values["embeddings.model"]

        if (
            not values.get("last_updated", None)
            and values.get("properties", {}).get("last_updated") is not None
            and values.get("properties", {}).get(
                "Last-Modified", values.get("properties", {}).get("last_updated")
            )
            is not None
        ):
            values["last_updated"] = values.get("properties", {}).get(
                "Last-Modified", values.get("properties", {}).get("last_updated")
            )

        return values


class SimpleSearchDocument(DocumentListItem):
    product: Annotated[Optional[str], OmitIfNone()] = Field("", description="label/title for the product.")
    content: Annotated[Optional[list[EntityContent]], OmitIfNone()] = Field(
        "", description="The content of the document that the vector matched."
    )
    summary: Annotated[Optional[str], OmitIfNone()] = Field(
        "", description="The summary for the document or a relevant part of the document."
    )
    dimensions: Annotated[Optional[dict[str, Any]], OmitIfNone()] = Field(
        None, description="The dimensions set on the document."
    )
    classification: Annotated[Optional[list[Classification]], OmitIfNone()] = Field(
        None, description="The classification set on the document."
    )
    ids: Annotated[Optional[list[ID]], OmitIfNone()] = Field(
        None, description="The IDs set on the document."
    )
    # metadata: Annotated[Optional[SearchMeta],OmitIfNone()] = Field(None, description='The meta data of the document.')

    def as_llm_content(self, content: [str] = None) -> [dict]:
        if content is None:
            content = ["content", "chunk"]
        the_content = " ".join([c.value for c in self.content if c.label in content or c.sub_type in content])
        return [
            {
                "content": f"Document ID: '{self.gid}',\nlabel: '{self.label}',\ndated: {self.last_updated},\nmain_url:'{self.gid_url}',\n{the_content} {self.product}"
            }
        ]

    def as_llm_str(self, content: [str] = None) -> [str]:
        if content is None:
            content = ["content", "chunk"]
        the_content = " ".join([c.value for c in self.content if c.label in content or c.sub_type in content])
        return [
            f"Document ID: '{self.gid}',\nlabel: '{self.label}',\ndated: {self.last_updated},\nmain_url:'{self.gid_url}',\n{the_content} {self.product}",
            self.content,
        ]


class SearchDocument(SimpleSearchDocument):

    type: str = Field(None, description="Document type.")
    variant: str = Field(None, description="Document variant.")
    last_updated: Optional[datetime.datetime] = Field(None, description="Document last updated.")
    # embedding: dict[str, Any] = Field([], description='Entity gid.')

    properties: Annotated[Optional[dict[str, Any]], OmitIfNone()] = Field(
        None, description="The properties set on the document."
    )
    dimensions: Annotated[Optional[dict[str, Any]], OmitIfNone()] = Field(
        None, description="The dimensions set on the document."
    )
    metrics: Annotated[Optional[dict[str, Any]], OmitIfNone()] = Field(
        None, description="The metrics set on the document."
    )
    flags: Annotated[Optional[dict[str, bool]], OmitIfNone()] = Field(
        None, description="The flags set on the document."
    )
    tags: Annotated[Optional[list[str]], OmitIfNone()] = Field(
        None, description="The tags set on the document."
    )
    classification: Annotated[Optional[list[Classification]], OmitIfNone()] = Field(
        None, description="The classification set on the document."
    )
    media: Annotated[Optional[list[Media]], OmitIfNone()] = Field(
        None, description="The classification set on the document."
    )
    ids: Annotated[Optional[list[ID]], OmitIfNone()] = Field(
        None, description="The IDs set on the document."
    )
    reranking: Annotated[Optional[DocumentReranking], OmitIfNone()] = Field(
        None, description="The dimensions set on the document."
    )
    cost: Annotated[Optional[LLMCost], OmitIfNone()] = Field(None, description="The cost of the search.")
    metadata: Annotated[Optional[SearchDocumentMeta], OmitIfNone()] = Field(
        None, description="The meta data of the document."
    )

    # summary: Annotated[Optional[str],OmitIfNone()] = Field(None, description='An automatically generated summary of the document, relevant to the query.')

    embeddings: Annotated[Optional[float], OmitIfNone()] = Field(
        description="The number of embeddings for this documet.", default=0
    )
    dist: Annotated[Optional[float], OmitIfNone()] = Field(
        description="The distance of the document.chunk from the query.", default=0
    )
    avg_dist: Annotated[Optional[float], OmitIfNone()] = Field(
        description="The average distance of the document from the query.", default=0
    )
    min_dist: Annotated[Optional[float], OmitIfNone()] = Field(
        description="The minimum distance of the document from the query.", default=0
    )
    max_dist: Annotated[Optional[float], OmitIfNone()] = Field(
        description="The maximum distance of the document from the query.", default=0
    )
    rank_weight: Annotated[Optional[float], OmitIfNone()] = Field(
        description="The minimum distance of the document from the query.", default=0
    )

    @model_validator(mode="before")
    def pre_init(cls, values):

        # check i if values extend BaseMode and convert to dict
        if issubclass(values.__class__, BaseModel):
            values = values.model_dump()

        if (
            not values.get("last_updated", None)
            and values.get("properties", {}).get("Last-Modified", values["properties"].get("last_updated"))
            is not None
        ):
            values["last_updated"] = values.get("properties", {}).get(
                "Last-Modified", values["properties"].get("last_updated")
            )

        if "updated" in values and not values.get("updated", None):
            del values["updated"]

        return values

    def as_simple_search_document(self, idx: int) -> SimpleSearchDocument:
        return SimpleSearchDocument(
            id=idx,
            label=self.label,
            product=self.product,
            content=self.content,
            last_updated=self.last_updated.isoformat() if self.last_updated else "",
        )


class DocumentSearchResultsMeta(SearchResultsMeta):
    documents_evaluated: Annotated[Optional[list[SimpleSearchDocument | SearchDocument]], OmitIfNone()] = (
        Field(None, description="The offset of the search.")
    )


class AnswerDocument(SearchBase):
    title: str = Field(None, description="The title of the document.")
    url: str = Field(None, description="The url of the document.")


class DocumentBasedAnswer(SearchBase):
    answer: str = Field(None, description="The answer to question.")
    rating: int = Field(None, description="Rate the answer from 1 to 10")
    question: str = Field(None, description="The question asked.")
    metadata: Annotated[Optional[DocumentSearchResultsMeta], OmitIfNone()] = Field(
        DocumentSearchResultsMeta(), description="Performance and outcome metadata of the search."
    )
    documents: Annotated[Optional[list[SimpleSearchDocument | SearchDocument]], OmitIfNone()] = Field(
        None, description="The documents used to answer the question."
    )
    cost: Annotated[Optional[list[LLMCost]], OmitIfNone()] = Field(
        None, description="The cost of the search."
    )


class LLMAnswer(SearchBase):
    answer: str = Field(None, description="The answer to question.")
    rating: int = Field(None, description="Rate the answer from 1 to 10")
    # documents: list[AnswerDocument] = Field(..., description='The documents used to answer the question.')


class SearchResults(SearchBase):
    documents: list[SimpleSearchDocument | SearchDocument] = Field(
        None, description="The documents found in the search."
    )
    metadata: DocumentSearchResultsMeta = Field(
        description="Performance and outcome metadata of the search.", default=None
    )
    cost: Optional[list[LLMCost]] = Field(description="The cost of the search.", default=None)

    def minimal_reply(self):
        return MinimalSearchResults(
            documents=[MinimalDocument(**d.model_dump()) for d in self.documents],
            metadata=self.metadata,
        )

    def list_reply(self):
        return MinimalSearchResults(
            documents=[DocumentListItem(**d.model_dump()) for d in self.documents],
            metadata=self.metadata,
        )


class MinimalSearchResults(SearchBase):
    presentation: Optional[str] = Field(description="The presentation rules", default=None)
    documents: list[MinimalDocument | DocumentListItem] = Field(
        None, description="The documents found in the search."
    )
    metadata: SearchDocumentMeta | DocumentSearchResultsMeta = Field(
        description="Performance and outcome metadata of the search.", default=None
    )
