from typing import Annotated, Optional

import pydantic
from pydantic import BaseModel, Field

from cxs.core.schema import OmitIfNone


class SearchBase(BaseModel):

    @pydantic.model_serializer
    def _serialize(self):
        omit_if_none_fields = {
            k for k, v in self.model_fields.items() if any(isinstance(m, OmitIfNone) for m in v.metadata)
        }
        return {k: v for k, v in self if k not in omit_if_none_fields or v is not None}


class SearchDocumentMeta(SearchBase):
    score: Annotated[Optional[float], OmitIfNone()] = Field(None, description="The score of the document.")
    updated: Annotated[Optional[str], OmitIfNone()] = Field(
        None, description="The content of the document that the vector matched."
    )
    no_parts: Annotated[Optional[float], OmitIfNone()] = Field(
        None, description="The number of sub documents found for this this document."
    )
    min_dist: Annotated[Optional[float], OmitIfNone()] = Field(
        None, description="The minimum distance of the document from the query."
    )
    max_dist: Annotated[Optional[float], OmitIfNone()] = Field(
        None, description="The maximum distance of the document from the query."
    )
    avg_dist: Annotated[Optional[float], OmitIfNone()] = Field(
        None, description="The average distance of the document from the query."
    )


class SearchResultsMeta(SearchBase):
    query_time: Annotated[Optional[float], OmitIfNone()] = Field(
        None, description="The time taken to run the search."
    )
    reranking_time: Annotated[Optional[float], OmitIfNone()] = Field(
        None, description="The time taken to run the search."
    )
    processing_time: Annotated[Optional[float], OmitIfNone()] = Field(
        None, description="The time taken to run the search."
    )
    embedding_time: Annotated[Optional[float], OmitIfNone()] = Field(
        None, description="The time taken to run the search."
    )
    llm_time: Annotated[Optional[float], OmitIfNone()] = Field(
        None, description="The time taken to run the LLM."
    )
    response_time: Annotated[Optional[float], OmitIfNone()] = Field(
        None, description="The total time taken to return the response."
    )
    total_found: Annotated[Optional[int], OmitIfNone()] = Field(
        None, description="The total number of documents found."
    )
    suppressed: Annotated[Optional[int], OmitIfNone()] = Field(
        None, description="The number of documents suppressed."
    )
    min_score: Annotated[Optional[int], OmitIfNone()] = Field(None, description="The minimum score filter.")
    offset: Annotated[Optional[int], OmitIfNone()] = Field(None, description="The offset of the search.")
