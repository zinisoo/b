from pydantic import BaseModel, HttpUrl
from typing import Optional

class MetadataCreate(BaseModel):
    target_url: HttpUrl
    target_name: Optional[str] = None
    raw_data: Optional[str] = None
