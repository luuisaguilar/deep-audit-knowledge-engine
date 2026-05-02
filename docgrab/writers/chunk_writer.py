import yaml
import logging
from pathlib import Path
from typing import List
from docgrab.models.chunk import SectionChunk

logger = logging.getLogger("docgrab.writers.chunk")

def write_chunks_manifest(chunks: List[SectionChunk], base_dir: Path) -> Path:
    """
    Writes all extracted chunks into a single aggregated YAML file.
    """
    output_path = base_dir / "chunks.yaml"
    
    # Serializing chunks
    data = [chunk.model_dump(mode="json") for chunk in chunks]
    
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)
        
    logger.info(f"Wrote {len(chunks)} chunks to {output_path}")
    return output_path
