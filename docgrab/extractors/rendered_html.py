import logging
import hashlib
from typing import List
from bs4 import BeautifulSoup
from playwright.sync_api import Page
from docgrab.models.page import ExtractedPage
from docgrab.cleaning.noise import find_main_content, clean_html_noise
from docgrab.config import Config
from docgrab.quality.scoring import calculate_extraction_score
from docgrab.discovery.spider import SIDEBAR_SELECTORS
from urllib.parse import urljoin, urlparse

logger = logging.getLogger("docgrab.extractors.rendered_html")

# Selectors that might trigger an expansion of a hidden menu
# aria-expanded="false" is common in modern React/Docusaurus docs
AUTO_EXPAND_SELECTORS = [
    "button[aria-expanded='false']",
    "li[aria-expanded='false']",
    ".menu__list-item--collapsed", # Docusaurus
    ".sidebar-nav-item.collapsed",
]

def expand_sidebar_menus(page: Page):
    """
    Finds and clicks potential expand/toggle buttons in doc sidebars.
    """
    logger.debug("Attempting to auto-expand collapsed sidebar menus...")
    
    # We focus on elements that look like toggles
    for selector in AUTO_EXPAND_SELECTORS:
        try:
            # We don't want to click infinite things, just what's initially collapsed
            elements = page.query_selector_all(selector)
            if elements:
                logger.debug(f"Found {len(elements)} potential collapsed elements for selector: {selector}")
                for el in elements:
                    if el.is_visible():
                        # Basic guard: don't click if it takes us away? 
                        # Usually these are buttons, not links.
                        el.click(timeout=1000)
                        # Small wait for animation
                        page.wait_for_timeout(200) 
        except Exception as e:
            logger.debug(f"Expansion failed for selector {selector}: {e}")

def extract_links_with_playwright(page: Page, root_url: str) -> List[str]:
    """
    Extracts internal links from known sidebar areas using Playwright selectors.
    Playwright pierces shadow DOM automatically!
    """
    links = set()
    
    def get_apex_domain(url):
        parsed = urlparse(url)
        parts = parsed.netloc.split('.')
        if len(parts) >= 2:
            return '.'.join(parts[-2:])
        return parsed.netloc

    root_apex = get_apex_domain(root_url)
    current_url = page.url
    
    # Try to find the best sidebar candidate via Playwright
    best_links = set()
    
    for selector in SIDEBAR_SELECTORS:
        try:
            # query_selector_all works across shadow boundaries for most selectors
            elements = page.query_selector_all(f"{selector} a[href]")
            if elements:
                current_candidate_links = set()
                logger.debug(f"Found {len(elements)} potential links in sidebar '{selector}' via Playwright.")
                for el in elements:
                    href = el.get_attribute("href")
                    if href:
                        full_url = urljoin(current_url, href).split("#")[0].split("?")[0]
                        link_apex = get_apex_domain(full_url)
                        if link_apex == root_apex:
                            if not any(full_url.lower().endswith(ext) for ext in [".png", ".jpg", ".pdf", ".zip", ".svg", ".css", ".js"]):
                                current_candidate_links.add(full_url)
                
                if len(current_candidate_links) > len(best_links):
                    best_links = current_candidate_links
                    logger.debug(f"New best Playwright sidebar candidate '{selector}' with {len(best_links)} internal links.")
        except Exception as e:
            logger.debug(f"Link extraction failed for selector {selector}: {e}")
            
    links = best_links
    
    # Bootstrap Fallback: If no sidebar links found, look in main content
    if not links:
        logger.info(f"No sidebar links found at {current_url} via Playwright. Bootstrapping from main content...")
        fallback_selectors = ["main", "article", "body"]
        for selector in fallback_selectors:
            try:
                elements = page.query_selector_all(f"{selector} a[href]")
                if elements:
                    for el in elements:
                        href = el.get_attribute("href")
                        if href:
                            full_url = urljoin(current_url, href).split("#")[0].split("?")[0]
                            link_apex = get_apex_domain(full_url)
                            if link_apex == root_apex:
                                if not any(full_url.lower().endswith(ext) for ext in [".png", ".jpg", ".pdf", ".zip", ".svg"]):
                                    links.add(full_url)
                    if links:
                        break # Found something
            except Exception:
                continue

    return sorted(list(links))

def extract_rendered_page(url: str, page: Page, config: Config) -> ExtractedPage:
    """
    Extracts content from a URL using a rendered Playwright page.
    Reuses the provided 'page' object (browser context).
    """
    try:
        logger.info(f"Navigating to {url} using Playwright...")
        
        # Navigate and wait for load
        page.goto(url, timeout=config.page_load_timeout, wait_until="networkidle")
        
        # Wait for custom selectors if provided
        if config.wait_selectors:
            for selector in config.wait_selectors:
                try:
                    logger.debug(f"Waiting for selector: {selector}")
                    page.wait_for_selector(selector, timeout=5000)
                except Exception as e:
                    logger.warning(f"Timeout waiting for selector {selector}: {e}")
        
        # New: Auto-expand sidebar menus to find hidden links
        expand_sidebar_menus(page)
        
        # New: Extract links using Playwright (Handles Shadow DOM)
        discovered_links = extract_links_with_playwright(page, config.root_url)

        # Get the rendered HTML
        content = page.content()
        try:
            soup = BeautifulSoup(content, 'lxml')
        except Exception:
            soup = BeautifulSoup(content, 'html.parser')
        
        # Extract title
        title_tag = soup.find('title')
        title = title_tag.text.strip() if title_tag else "Untitled"
        
        # Find main content
        main_content_soup = find_main_content(soup)
        
        # Clean noise
        cleaned_soup = clean_html_noise(main_content_soup)
        
        # Calculate content hash
        content_str = cleaned_soup.decode_contents()
        word_cnt = len(content_str.split())
        content_hash = hashlib.sha256(content_str.encode('utf-8')).hexdigest()
        
        return ExtractedPage(
            title=title,
            source_url=url,
            relative_path=url,
            raw_html=content,
            clean_markdown=None,
            word_count=word_cnt,
            content_hash=content_hash,
            extraction_mode="rendered",
            discovered_links=discovered_links,
            extraction_score=calculate_extraction_score(cleaned_soup, word_cnt)
        )
        
    except Exception as e:
        logger.error(f"Rendered extraction failed for {url}: {e}")
        return ExtractedPage(
            title="Error",
            source_url=url,
            relative_path=url,
            content_hash="error",
            status="failure",
            error_message=str(e),
            extraction_mode="rendered"
        )
