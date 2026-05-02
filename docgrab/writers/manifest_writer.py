import yaml
import logging
from pathlib import Path
from docgrab.models.manifest import CorpusManifest

logger = logging.getLogger("docgrab.writers.manifest")

def write_manifest(manifest: CorpusManifest, base_dir: Path) -> Path:
    """
    Writes the final corpus manifest to YAML.
    """
    output_path = base_dir / "manifest.yaml"
    
    # Using model_dump (Pydantic v2) to get a dict
    manifest_data = manifest.model_dump(mode="json")
    
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(manifest_data, f, sort_keys=False, allow_unicode=True)
        
    logger.info(f"Wrote manifest to {output_path}")
    return output_path
