import logging
from bs4 import BeautifulSoup

logger = logging.getLogger("docgrab.cleaning.noise")

def clean_html_noise(soup: BeautifulSoup) -> BeautifulSoup:
    """
    Remove common documentation noise tags like nav, footer, sidebars, etc.
    """
    # Common semantic tags that are usually noise in a doc context
    noise_tags = [
        'nav', 'footer', 'aside', 'header', 
        'script', 'style', 'iframe', 'noscript',
        'form', 'button', 'input', 'label'
    ]
    
    # Common classes/IDs that represent noise
    noise_selectors = [
        '.sidebar', '.navigation', '.footer', '.breadcrumb',
        '.cookie-banner', '.feedback-block', '.ad-block',
        '.social-share', '#sidebar', '#footer', '#navigation'
    ]
    
    # Remove by tag
    for tag in noise_tags:
        for element in soup.find_all(tag):
            element.decompose()
            
    # Remove by CSS selector
    for selector in noise_selectors:
        for element in soup.select(selector):
            element.decompose()
            
    return soup

def find_main_content(soup: BeautifulSoup) -> BeautifulSoup:
    """
    Heuristic to find the main content of a documentation page.
    Look for <main>, <article>, or classes like 'content', 'main-content'.
    """
    # Priority order for finding content
    candidates = [
        soup.find('main'),
        soup.find('article'),
        soup.find(class_=lambda x: x and ('content' in x or 'main' in x) and 'sidebar' not in x),
        soup.find(id=lambda x: x and ('content' in x or 'main' in x))
    ]
    
    for candidate in candidates:
        if candidate:
            logger.debug(f"Found content candidate using heuristic.")
            return candidate
            
    # Fallback to body if nothing else found
    return soup.find('body') or soup
