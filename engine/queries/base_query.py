from typing import Mapping
from pydantic import BaseModel, Field

from engine.records.types.record_type import RecordType


class BaseQuery(BaseModel):
    query_type: str
    update: Mapping[int, RecordType] = Field(discriminator="record_type")
