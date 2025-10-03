from pydantic import BaseModel, Field
from typing import Optional

import uuid

class ServiceParams(BaseModel):
    action: str = Field(description="If a curser is used to fetch pages then this is it", default="")
    service: str = Field(description="If a curser is used to fetch pages then this is it", default="")
    component_id: uuid.UUID = Field(description="", default=None)
    service_id: Optional[uuid.UUID] = Field(description="", default=None)

    items: Optional[int] = Field(description="", default=100, gt=0, le=100)
    offset: Optional[int] = Field(description="", default=0, ge=0)
    cursor: str = Field(description="If a curser is used to fetch pages then this is it", default="")
    model_config = {"extra": "allow"}
