import logging
import requests
from typing import List, Set
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

logger = logging.getLogger("docgrab.discovery.sitemap")

def discover_urls_from_sitemap(sitemap_url: str, session: requests.Session) -> List[str]:
    """
    Recursively discovers URLs from a sitemap or sitemap index.
    """
    urls: Set[str] = set()
    try:
        response = session.get(sitemap_url)
        response.raise_for_status()
        
        # Remove namespaces for easier parsing or handle them properly
        # Common approach: use {http://www.sitemaps.org/schemas/sitemap/0.9}
        root = ET.fromstring(response.content)
        tag = root.tag.split('}')[-1]
        
        if tag == "sitemapindex":
            logger.info(f"Detected sitemap index: {sitemap_url}")
            for sitemap in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
                urls.update(discover_urls_from_sitemap(sitemap.text, session))
        elif tag == "urlset":
            logger.info(f"Detected urlset: {sitemap_url}")
            for loc in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
                urls.add(loc.text)
        else:
            logger.warning(f"Unknown sitemap tag <{tag}> at {sitemap_url}")
            
    except Exception as e:
        logger.error(f"Failed to parse sitemap at {sitemap_url}: {e}")
        
    return sorted(list(urls))
