from enum import Enum
from typing import *
from datetime import datetime
from pydantic import Field
from cxs.core.schema import CXSBase, empty_list, OmitIfNone

class InteractionRole(Enum):
    ai = "ai"
    agent = "agent"
    user = "user"
    system = "system"

class Interaction(CXSBase):
    role: InteractionRole = Field(description="Role of the user in the conversation", default=None)
    content: str = Field(description="Content of the interaction", default=None)
    at: datetime = Field(description="Time when the interaction occurred", default=None)

class ConversationTranscript(CXSBase):
    interactions: List[Interaction] = Field(description="List of interactions in the conversation", default_factory=empty_list)
    started_at: Annotated[Optional[datetime], OmitIfNone()] = Field(description="Time when the conversation started", default=None)
    ended_at: datetime = Field(description="Time when the conversation ended", default=None)
