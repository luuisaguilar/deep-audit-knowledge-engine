from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class ExtractedPage(BaseModel):
    """
    Represents a single extracted documentation page.
    """
    title: str
    source_url: str
    relative_path: str
    raw_html: Optional[str] = None
    clean_markdown: Optional[str] = None
    word_count: int = 0
    content_hash: str
    headings: List[str] = []
    discovered_links: List[str] = []
    internal_links_count: int = 0
    extraction_score: float = 0.0
    extraction_mode: str = "static"  # static, rendered, repo, pdf
    status: str = "success"  # success, failure, skipped
    error_message: Optional[str] = None
    extracted_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = {}
