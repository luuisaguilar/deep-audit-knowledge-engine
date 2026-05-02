import logging
import requests
import hashlib
from bs4 import BeautifulSoup
from docgrab.models.page import ExtractedPage
from docgrab.cleaning.noise import find_main_content, clean_html_noise

logger = logging.getLogger("docgrab.extractors.static_html")

def extract_static_page(url: str, session: requests.Session) -> ExtractedPage:
    """
    Fetches a page and extracts its content using static analysis.
    """
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Extract title
        title_tag = soup.find('title')
        title = title_tag.text.strip() if title_tag else "Untitled"
        
        # Find main content before cleaning (better context)
        main_content_soup = find_main_content(soup)
        
        # Clean noise from the relevant section
        cleaned_soup = clean_html_noise(main_content_soup)
        
        # Calculate content hash for dedupe
        content_str = cleaned_soup.decode_contents()
        content_hash = hashlib.sha256(content_str.encode('utf-8')).hexdigest()
        
        return ExtractedPage(
            title=title,
            source_url=url,
            relative_path=url, # Will be normalized by writer
            raw_html=response.text,
            clean_markdown=None, # To be filled by markdown writer
            word_count=len(content_str.split()),
            content_hash=content_hash,
            extraction_mode="static"
        )
        
    except Exception as e:
        logger.error(f"Failed to extract page at {url}: {e}")
        return ExtractedPage(
            title="Error",
            source_url=url,
            relative_path=url,
            content_hash="error",
            status="failure",
            error_message=str(e)
        )
