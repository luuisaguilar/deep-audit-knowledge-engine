import logging
import requests
from playwright.sync_api import Page
from typing import Optional

from docgrab.config import Config
from docgrab.models.page import ExtractedPage
from docgrab.extractors.static_html import extract_static_page
from docgrab.extractors.rendered_html import extract_rendered_page
from docgrab.quality.scoring import calculate_extraction_score
from bs4 import BeautifulSoup

logger = logging.getLogger("docgrab.extractors.strategy")

def execute_extraction(
    url: str, 
    mode: str, 
    config: Config, 
    session: requests.Session, 
    playwright_page: Optional[Page] = None
) -> ExtractedPage:
    """
    Executes the extraction based on the selected mode and fallback logic.
    
    Modes:
    - static: Only use BeautifulSoup + requests.
    - rendered: Only use Playwright.
    - auto: Try static first, fallback to rendered if quality is low or fails.
    """
    
    if mode == "static":
        return extract_static_page(url, session)
        
    if mode == "rendered":
        if not playwright_page:
            raise ValueError("Playwright page required for 'rendered' mode.")
        return extract_rendered_page(url, playwright_page, config)
        
    # auto mode logic
    logger.debug(f"Attempting 'auto' extraction for {url}")
    
    # 1. Try static
    page_data = extract_static_page(url, session)
    
    # Calculate score for decision
    if page_data.status == "success" and page_data.raw_html:
        soup = BeautifulSoup(page_data.raw_html, 'lxml')
        score = calculate_extraction_score(soup, page_data.word_count)
        page_data.extraction_score = score
    else:
        score = 0.0

    # 2. Check fallback triggers
    should_fallback = False
    reason = ""
    
    if page_data.status == "failure":
        should_fallback = True
        reason = "static extraction failed"
    elif page_data.word_count < 50:
        should_fallback = True
        reason = f"content too small ({page_data.word_count} words)"
    elif score < config.fallback_threshold:
        should_fallback = True
        reason = f"low quality score ({score:.2f} < {config.fallback_threshold})"

    if should_fallback:
        if playwright_page:
            logger.info(f"Fallback triggered for {url}: {reason}. Retrying with Playwright.")
            rendered_data = extract_rendered_page(url, playwright_page, config)
            # Tag the mode to show it was a fallback
            rendered_data.extraction_mode = "auto(rendered)"
            # Ensure score is computed for the rendered version too
            if rendered_data.status == "success" and rendered_data.raw_html:
                r_soup = BeautifulSoup(rendered_data.raw_html, 'lxml')
                rendered_data.extraction_score = calculate_extraction_score(r_soup, rendered_data.word_count)
            return rendered_data
        else:
            logger.warning(f"Fallback indicated for {url} ({reason}), but Playwright is not available.")
            page_data.extraction_mode = "auto(static)"
            return page_data

    # If no fallback needed, return the static result tagged as auto
    page_data.extraction_mode = "auto(static)"
    return page_data
