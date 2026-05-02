import logging
from typing import Dict, Optional, Set
from docgrab.utils.url import normalize_url

logger = logging.getLogger("docgrab.utils.dedupe")

class DedupeManager:
    """
    Manages URL and content hash deduplication across a crawl run.
    """
    def __init__(self):
        # Maps normalized URL -> boolean (seen)
        self.seen_urls: Set[str] = set()
        
        # Maps content hash -> canonical source URL
        self.seen_hashes: Dict[str, str] = {}

    def is_url_seen(self, url: str) -> bool:
        """
        Check if a normalized URL has already been processed or scheduled.
        """
        norm_url = normalize_url(url)
        if norm_url in self.seen_urls:
            return True
        self.seen_urls.add(norm_url)
        return False

    def get_duplicate_target(self, content_hash: str) -> Optional[str]:
        """
        Check if a content hash has been seen. Returns the canonical URL if so.
        """
        return self.seen_hashes.get(content_hash)

    def register_content(self, url: str, content_hash: str):
        """
        Registers a content hash for a canonical URL.
        """
        if content_hash not in self.seen_hashes:
            self.seen_hashes[content_hash] = url
        else:
            logger.debug(f"Content hash {content_hash} already registered for {self.seen_hashes[content_hash]}")
