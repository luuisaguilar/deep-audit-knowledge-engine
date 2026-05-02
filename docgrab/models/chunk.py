from pydantic import BaseModel
from typing import List, Optional

class SectionChunk(BaseModel):
    """
    Represents a chunked section of a page (Sprint 2+).
    """
    chunk_id: str
    page_url: str
    page_title: str
    heading_path: List[str]
    heading_level: int
    content: str
    word_count: int
    content_hash: str
