from pydantic import BaseModel, HttpUrl
from typing import Optional, List

class SiteInfo(BaseModel):
    """
    Metadata about the target documentation site.
    """
    base_url: str
    sitemap_url: Optional[str] = None
    framework: Optional[str] = None
    pages_discovered: int = 0
