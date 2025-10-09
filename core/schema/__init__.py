from cxs.core.utils.schema_builder import ExtendableBaseModel

__import__("pkg_resources").declare_namespace(__name__)

import pydantic

from pydantic import BaseModel
from dataclasses import dataclass

@dataclass
class OmitIfNone:
    pass

def empty_list():
    return []

def empty_dict():
    return {}

class CXSSchema(BaseModel):

    @pydantic.model_serializer
    def _serialize(self):
        omit_if_none_fields = {
            k
            for k, v in self.model_fields.items()
            if any(isinstance(m, OmitIfNone) for m in v.metadata)
        }
        return {k: v for k, v in self if k not in omit_if_none_fields or v is not None}

class CXSBase(ExtendableBaseModel):

    @pydantic.model_serializer
    def _serialize(self):
        omit_if_none_fields = {
            k
            for k, v in self.model_fields.items()
            if any(isinstance(m, OmitIfNone) for m in v.metadata)
        }
        return {k: v for k, v in self if k not in omit_if_none_fields or v}
