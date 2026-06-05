from typing import Optional
from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel


class UrlModel(BaseModel):
    slug: str
    target_url: AnyHttpUrl
    expires_at: Optional[datetime] = None
