from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SystemMetadataCreate(BaseModel):
    key: str = Field(min_length=1, max_length=128)
    value: str | None = Field(default=None, max_length=512)


class SystemMetadataRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    value: str | None
    created_at: datetime
    updated_at: datetime
