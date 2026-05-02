import os
import logging
from typing import List, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from pathlib import Path

logger = logging.getLogger("docgrab.discovery.spider")

# Common sidebar selectors found in documentation tools (Docusaurus, GitBook, Sphinx, etc.)
SIDEBAR_SELECTORS = [
    "nav", 
    "aside", 
    "[role='navigation']", 
    "#sidebar", 
    ".sidebar", 
    ".navigation",
    ".menu",
    ".docs-sidebar",
    ".docs-nav",
    ".td-sidebar", # Docsy
    "#toc",        # Proxmox / MediaWiki style
    ".toc",        # Generic TOC
    ".sidebar-container",
    ".sidebar-nav",
    ".css-175oi2r", # React Native / Expo style sidebars sometimes use these hashes
    "div[class*='sidebar']",
    "nav[class*='nav']",
    "div[class*='navigation']",
    "div[class*='menu']",
    "aside[class*='sidebar']",
    ".lg\\:w-72", # BuilderBot / Tailwind style fixed sidebars
    ".lg\\:w-64",
    "div.contents" # Sometimes used as a wrapper for sidebar contents
]

def extract_sidebar_links(html: str, current_url: str, root_url: str) -> List[str]:
    """
    Extracts internal links found specifically within sidebar/navigation elements.
    """
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")
    links: Set[str] = set()
    
    # Try to find the best sidebar candidate (the one with the most internal links)
    best_sidebar = None
    max_links = 0
    
    for selector in SIDEBAR_SELECTORS:
        try:
            # Handle colons in selectors for BeautifulSoup (Tailwind classes)
            if ":" in selector and selector.startswith("."):
                # Use attribute selector for classes with colons
                clean_cls = selector.strip(".")
                candidates = soup.find_all(class_=clean_cls)
            else:
                candidates = soup.select(selector)
                
            for candidate in candidates:
                links_in_candidate = candidate.find_all("a", href=True)
                if len(links_in_candidate) > max_links:
                    max_links = len(links_in_candidate)
                    best_sidebar = candidate
                    logger.debug(f"New best sidebar found via '{selector}' with {max_links} links.")
        except Exception as e:
            logger.debug(f"Selector '{selector}' failed: {e}")
            
    sidebar = best_sidebar
    if sidebar:
        logger.info(f"Selected sidebar with {max_links} links.")
            
    # Fallback: If no dedicated sidebar container is found, look for links in the main content area.
    # This is common on landing/index pages that link to sub-guides.
        # Fallback 1: Look for links inside <li> elements (very common for docs nav)
        logger.info(f"No sidebar found at {current_url}. Trying list-based discovery...")
        li_links = soup.find_all("li")
        if len(li_links) > 5: # Threshold to avoid random small lists
            sidebar = soup # Use the whole soup but we'll focus on these links if we wanted to
            # But actually, the current loop below will just find all links in 'sidebar'
            # So if we set sidebar = soup, it finds everything.
        else:
            sidebar = soup.find("main") or soup.find("article") or soup.find("body")
            
        if not sidebar:
            return []

    def get_apex_domain(url):
        parsed = urlparse(url)
        parts = parsed.netloc.split('.')
        if len(parts) >= 2:
            return '.'.join(parts[-2:])
        return parsed.netloc

    root_apex = get_apex_domain(root_url)
    
    for a in sidebar.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(current_url, href)
        
        # Clean fragment and query
        full_url = full_url.split("#")[0].split("?")[0]
        
        # Filter internal links by apex domain
        parsed = urlparse(full_url)
        link_apex = get_apex_domain(full_url)
        
        if link_apex == root_apex:
            # Ensure it's not an asset
            if not any(full_url.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".svg", ".css", ".js"]):
                links.add(full_url)
            else:
                logger.debug(f"Filtering out asset link: {full_url}")
        else:
            logger.debug(f"Filtering out external link: {full_url} (Root apex: {root_apex})")
                
    return sorted(list(links))

def get_hierarchical_path(url: str, root_url: str) -> Path:
    """
    Derives a relative file path from a URL, relative to the root URL.
    Example:
    root: https://example.com/docs
    url: https://example.com/docs/agent/models
    yields: agent/models
    """
    parsed_root = urlparse(root_url.rstrip("/"))
    parsed_url = urlparse(url.rstrip("/"))
    
    root_path = parsed_root.path
    url_path = parsed_url.path
    
    if url_path.startswith(root_path):
        rel_path = os.path.relpath(url_path, root_path)
        if rel_path == ".":
            return Path("index")
        return Path(rel_path)
    
    # Fallback to just the last part if not under root path
    return Path(url_path.strip("/")).name or Path("index")
