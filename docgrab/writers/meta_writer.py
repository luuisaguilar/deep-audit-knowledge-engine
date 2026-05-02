import yaml
import logging
from pathlib import Path
from docgrab.models.page import ExtractedPage
from docgrab.utils.path import sanitize_filename

logger = logging.getLogger("docgrab.writers.meta")

def write_page_metadata(page: ExtractedPage, base_dir: Path) -> Path:
    """
    Writes individual page metadata to a YAML file.
    """
    meta_dir = base_dir / "meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    
    # Same naming logic as markdown writer
    filename = page.title.lower().replace(" ", "_") + ".yaml"
    if page.source_url:
        path_segments = [s for s in page.source_url.split('/') if s]
        if path_segments:
            filename = path_segments[-1].replace(".html", "").replace(".md", "") + ".yaml"
            
    filename = sanitize_filename(filename)
    output_path = meta_dir / filename
    
    # Convert to dict, excluding raw content for the meta file
    meta_data = page.model_dump(
        exclude={"raw_html", "clean_markdown"},
        mode="json"
    )
    
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(meta_data, f, sort_keys=False, allow_unicode=True)
        
    return output_path
