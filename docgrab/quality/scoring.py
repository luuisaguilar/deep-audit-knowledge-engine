import logging
from bs4 import BeautifulSoup
import re

logger = logging.getLogger("docgrab.quality.scoring")

def calculate_extraction_score(soup: BeautifulSoup, word_count: int) -> float:
    """
    Computes a deterministic extraction quality score in range [0.0, 1.0].
    
    Factors:
    - Minimum word threshold (penalizes very short pages)
    - Heading density
    - Code block presence
    - Link density (high density often indicates a navigation/index page vs content)
    - Noise remnants (penalizes suspicious keywords)
    """
    score = 0.5 # Baseline
    
    # 1. Word Count Penalty/Bonus
    if word_count < 20:
        score -= 0.3 # High penalty for nearly empty pages
    elif word_count > 100:
        score += 0.1 # Bonus for substantial content
        
    # 2. Structural Elements (Headings)
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    if headings:
        score += 0.2
    else:
        score -= 0.2 # Docs usually have headings
        
    # 3. Structural Elements (Code Blocks)
    code_blocks = soup.find_all(['pre', 'code'])
    if code_blocks:
        score += 0.1 # Bonus for technical docs
        
    # 4. Link Density Check
    links = soup.find_all('a')
    if word_count > 0:
        link_density = len(links) / word_count
        if link_density > 0.5:
            score -= 0.2 # Likely a directory or nav list
            
    # 5. Suspicious Noise (Remaining in cleaned soup)
    noise_keywords = ["cookie", "subscribe", "newsletter", "advertisement", "copyright"]
    text = soup.get_text().lower()
    for kw in noise_keywords:
        if kw in text:
            score -= 0.05
            
    # Normalize to [0.0, 1.0]
    return max(0.0, min(1.0, score))
