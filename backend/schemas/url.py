from typing import Optional
from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel


class CreateUrlRequest(BaseModel):
    target_url: AnyHttpUrl
    slug: Optional[str] = None
    # lifetime in seconds
    ttl: Optional[int] = None
    # reuse existing slug if target_url already shortened
    reuse_existing: bool = False


class UrlResponse(BaseModel):
    slug: str
    short_url: AnyHttpUrl
    target_url: AnyHttpUrl
    expires_at: Optional[datetime] = None
