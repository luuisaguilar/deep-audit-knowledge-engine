from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ManifestPage(BaseModel):
    """
    Summary of an extracted page for the manifest.
    """
    title: str
    source_url: str
    output_file: str
    word_count: int
    content_hash: str
    extraction_mode: str
    status: str
    extraction_score: float = 0.0
    duplicate_of: Optional[str] = None
    chunk_count: int = 0

class CorpusManifest(BaseModel):
    """
    Root manifest for an extraction run.
    """
    run_id: str
    root_url: str
    extracted_at: datetime = Field(default_factory=datetime.now)
    total_pages: int = 0
    pages: List[ManifestPage] = []
