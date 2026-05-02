import os
import logging
from pathlib import Path
from markdownify import markdownify
from docgrab.models.page import ExtractedPage
from docgrab.utils.path import sanitize_filename

logger = logging.getLogger("docgrab.writers.markdown")

def write_page_as_markdown(page: ExtractedPage, base_dir: Path) -> Path:
    """
    Converts extracted content to Markdown and writes it to disk.
    """
    # Create directory structure
    pages_dir = base_dir / "pages"
    
    # Use relative_path if available (from spidering)
    if getattr(page, "relative_path", None) and page.relative_path != page.source_url:
        # relative_path like "agent/models"
        # Sanitize each segment for Windows compatibility
        safe_segments = [sanitize_filename(s) for s in page.relative_path.split("/") if s]
        rel_path = Path(*safe_segments)
        
        # Ensure we always use .md extension for converted content
        if rel_path.suffix.lower() in [".html", ".htm", ""]:
            output_path = pages_dir / rel_path.with_suffix(".md")
        else:
            output_path = pages_dir / rel_path
    else:
        # Fallback to sanitized filename logic
        filename = page.title.lower().replace(" ", "_") + ".md"
        if page.source_url:
            path_segments = [s for s in page.source_url.split('/') if s]
            if path_segments:
                filename = path_segments[-1].replace(".html", "") + ".md"
        
        filename = sanitize_filename(filename)
        output_path = pages_dir / filename
    
    # Ensure parent directory exists for nested paths
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert HTML to Markdown
    # We use some options to keep code blocks clean
    markdown_content = markdownify(
        page.raw_html or "", 
        heading_style="ATX",
        code_language_callback=lambda el: el.get('class', [''])[0].replace('language-', '') if el.get('class') else ''
    )
    
    # Prepend YAML frontmatter
    frontmatter = f"""---
title: {page.title}
source_url: {page.source_url}
extracted_at: {page.extracted_at.isoformat()}
content_hash: {page.content_hash}
---

"""
    final_content = frontmatter + markdown_content
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_content)
        
    logger.info(f"Wrote markdown to {output_path}")
    return output_path
