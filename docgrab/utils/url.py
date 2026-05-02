import re
from urllib.parse import urlparse, urljoin, urldefrag

def normalize_url(url: str, base_url: str = "") -> str:
    """
    Standardizes a URL by joining with base, removing fragments, 
    and ensuring consistent trailing slashes.
    """
    # Join with base if relative
    full_url = urljoin(base_url, url)
    
    # Remove fragments (#...)
    defragmented, _ = urldefrag(full_url)
    
    # Normalize by removing trailing slash for consistent deduplication
    defragmented = defragmented.rstrip('/')
        
    return defragmented

def is_internal_url(url: str, base_url: str) -> bool:
    """
    Checks if a URL belongs to the same domain as the base URL.
    """
    base_netloc = urlparse(base_url).netloc
    url_netloc = urlparse(url).netloc
    return url_netloc == "" or url_netloc == base_netloc

def is_asset_url(url: str) -> bool:
    """
    Identify if a URL points to a static asset that should be ignored.
    """
    asset_extensions = {
        '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
        '.css', '.js', '.woff', '.woff2', '.ttf', '.eot',
        '.mp4', '.webm', '.ogv', '.mp3', '.wav', '.flac',
        '.zip', '.tar', '.gz', '.7z', '.exe', '.dmg', '.pkg',
        '.pdf' # PDF is Sprint 5
    }
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in asset_extensions)
