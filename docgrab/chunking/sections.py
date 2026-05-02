import logging
import hashlib
from typing import List, Optional
from bs4 import BeautifulSoup, NavigableString, Tag
from docgrab.models.chunk import SectionChunk
from docgrab.utils.url import normalize_url

logger = logging.getLogger("docgrab.chunking.sections")

def chunk_html_by_sections(
    url: str, 
    page_title: str, 
    soup: BeautifulSoup
) -> List[SectionChunk]:
    """
    Splits cleaned HTML into chunks based on heading (h1-h6) hierarchy.
    Maintains the heading path to provide context for sub-sections.
    """
    final_chunks: List[SectionChunk] = []
    norm_url = normalize_url(url)
    
    # Track current heading hierarchy stack
    # stack of (level, text)
    heading_stack: List[tuple[int, str]] = []
    
    # Temporary storage for current section content
    current_content: List[str] = []

    def push_final_chunk(last_content: List[str], current_stack: List[tuple[int, str]]):
        if not last_content:
            return
            
        full_text = "".join(last_content).strip()
        if not full_text:
            return
            
        path = [h[1] for h in current_stack]
        level = current_stack[-1][0] if current_stack else 0
        
        # Calculate deterministic chunk ID
        # ID = hash(norm_url + "|".join(path) + normalized_content)
        # We use a mix of URL, Path and Content snippet for stable uniqueness
        content_hash = hashlib.sha256(full_text.encode('utf-8')).hexdigest()
        id_material = f"{norm_url}|{'|'.join(path)}|{full_text.strip()[:200]}"
        chunk_id = hashlib.sha256(id_material.encode('utf-8')).hexdigest()
        
        final_chunks.append(SectionChunk(
            chunk_id=chunk_id,
            page_url=url,
            page_title=page_title,
            heading_path=path,
            heading_level=level,
            content=full_text,
            word_count=len(full_text.split()),
            content_hash=content_hash
        ))

    # If we have a single child wrapper (like a div#content), descend into it
    content_root = soup
    while True:
        # Filter for meaningful children
        kids = [c for c in content_root.children if isinstance(c, Tag) or (isinstance(c, NavigableString) and c.strip())]
        if len(kids) == 1 and isinstance(kids[0], Tag) and kids[0].name in ['div', 'main', 'article', 'section', 'body', 'html']:
            content_root = kids[0]
        else:
            break

    # Iterate through direct children of the identified content root
    for element in content_root.children:
        if isinstance(element, Tag) and element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            # Push the previous section before starting new one
            push_final_chunk(current_content, heading_stack)
            current_content = []
            
            level = int(element.name[1])
            text = element.get_text().strip()
            
            # Update stack: pop elements that are deeper than or equal to current level
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            
            heading_stack.append((level, text))
            
            # Keep the header in the chunk content for visual structure
            current_content.append(str(element))
            
        else:
            # Accumulate normal content (tags or text)
            current_content.append(str(element))
            
    # Final flush for the last section
    push_final_chunk(current_content, heading_stack)
    
    return final_chunks
