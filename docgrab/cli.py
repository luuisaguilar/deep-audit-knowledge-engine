import logging
import requests
import typer
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from docgrab.config import Config
from docgrab.logging import setup_logging
from docgrab.discovery.sitemap import discover_urls_from_sitemap
from docgrab.extractors.strategy import execute_extraction
from docgrab.models.manifest import CorpusManifest, ManifestPage
from docgrab.models.site import SiteInfo
from docgrab.utils.dedupe import DedupeManager
from docgrab.quality.scoring import calculate_extraction_score
from docgrab.chunking.sections import chunk_html_by_sections
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from docgrab.discovery.spider import extract_sidebar_links, get_hierarchical_path

from docgrab.writers.markdown_writer import write_page_as_markdown
from docgrab.writers.meta_writer import write_page_metadata
from docgrab.writers.chunk_writer import write_chunks_manifest
from docgrab.writers.manifest_writer import write_manifest

app = typer.Typer(help="DocGrab — Documentation Extraction Framework")

@app.command()
def run(
    url: str = typer.Option(..., "--url", "-u", help="Root documentation URL or Sitemap URL"),
    out: Path = typer.Option(Path("./exports"), "--out", "-o", help="Output directory"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of pages to extract"),
    mode: str = typer.Option("auto", "--mode", "-m", help="Extraction mode: auto, static, rendered"),
    wait_selector: Optional[List[str]] = typer.Option(None, "--wait-selector", "-w", help="Selectors to wait for in rendered mode"),
    max_depth: int = typer.Option(5, "--max-depth", "-d", help="Maximum recursion depth for discovery"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """
    Run the documentation extraction pipeline.
    """
    setup_logging(level=logging.DEBUG if verbose else logging.INFO)
    logger = logging.getLogger("docgrab")
    
    logger.info(f"Starting DocGrab for {url}")
    
    # 1. Setup Output & Managers
    out_path = Path(out)
    out_path.mkdir(parents=True, exist_ok=True)
    
    config = Config(
        root_url=url,
        output_dir=out_path,
        wait_selectors=wait_selector or []
    )
    
    session = requests.Session()
    session.headers.update({"User-Agent": config.user_agent})
    
    dedupe = DedupeManager()
    all_chunks = []
    
    # 2. Discovery Setup
    to_visit = set()
    visited = set()
    
    sitemap_url = url if url.endswith(".xml") else f"{url.rstrip('/')}/sitemap.xml"
    logger.info(f"Searching for sitemaps at: {sitemap_url}")
    
    sitemap_urls = discover_urls_from_sitemap(sitemap_url, session)
    if sitemap_urls:
        to_visit.update(sitemap_urls)
    else:
        logger.warning("No URLs found via sitemap. Seeding with root URL.")
        to_visit.add(url)
        
    logger.info(f"Initial discovery found {len(to_visit)} pages.")
    
    # 3. Extraction & Processing
    manifest_pages = []
    
    # Browser Context Management
    playwright_context = None
    browser = None
    pw_page = None
    
    try:
        if mode in ["auto", "rendered"]:
            logger.info("Initializing Playwright (Chromium)...")
            playwright_context = sync_playwright().start()
            browser = playwright_context.chromium.launch(headless=True)
            pw_page = browser.new_page()

        # We use a simple while loop for dynamic discovery
        processed_count = 0
        while to_visit:
            if limit and processed_count >= limit:
                logger.info(f"Reached page limit ({limit}). Stopping.")
                break
                
            page_url = sorted(list(to_visit))[0] # Deterministic order
            to_visit.remove(page_url)
            
            if page_url in visited:
                continue
            
            visited.add(page_url)
            logger.info(f"[{processed_count+1}] Processing: {page_url}")

            try:
                # Extraction with Strategy Selection
                page = execute_extraction(
                    url=page_url, 
                    mode=mode, 
                    config=config, 
                    session=session, 
                    playwright_page=pw_page
                )
                
                if page.status == "success":
                    processed_count += 1
                    
                    # Discovery: Use links found by the extractor (Playwright handles shadow DOM better)
                    new_links = page.discovered_links if page.discovered_links else extract_sidebar_links(page.raw_html, page_url, url)
                    new_added = 0
                    for link in new_links:
                        if link not in visited and link not in to_visit:
                            to_visit.add(link)
                            new_added += 1
                    if new_added:
                        logger.info(f"🔍 Discovered {new_added} new unique links.")
                    elif not page.discovered_links:
                        logger.debug("No new links found in sidebar.")

                    # Content-hash dedupe
                    duplicate_of = dedupe.get_duplicate_target(page.content_hash)
                    
                    if duplicate_of:
                        logger.debug(f"🔗 Content duplicate detected for {page_url}")
                        page.status = "duplicate"
                        manifest_pages.append(ManifestPage(
                            title=page.title,
                            source_url=page.source_url,
                            output_file="[DUPLICATE]",
                            word_count=page.word_count,
                            content_hash=page.content_hash,
                            extraction_mode=page.extraction_mode,
                            status="duplicate",
                            duplicate_of=duplicate_of
                        ))
                        continue

                    # Register canonical content
                    dedupe.register_content(page.source_url, page.content_hash)

                    # Hierarchical Path Calculation
                    rel_path = get_hierarchical_path(page_url, url)
                    page.relative_path = str(rel_path)

                    # Logic for Quality/Scoring/Chunking
                    temp_soup = BeautifulSoup(page.raw_html, "lxml") if page.raw_html else BeautifulSoup("", "lxml")
                    chunks = chunk_html_by_sections(page.source_url, page.title, temp_soup)
                    all_chunks.extend(chunks)
                    
                    page.headings = [c.heading_path[-1] for c in chunks if c.heading_path]
                    
                    # Write Outputs
                    md_path = write_page_as_markdown(page, out_path)
                    write_page_metadata(page, out_path)
                    
                    manifest_pages.append(ManifestPage(
                        title=page.title,
                        source_url=page.source_url,
                        output_file=str(md_path.relative_to(out_path)),
                        word_count=page.word_count,
                        content_hash=page.content_hash,
                        extraction_mode=page.extraction_mode,
                        status="success",
                        extraction_score=page.extraction_score,
                        chunk_count=len(chunks)
                    ))
                else:
                    logger.error(f"❌ Failed to extract {page_url}: {page.error_message}")
                    manifest_pages.append(ManifestPage(
                        title="Error",
                        source_url=page_url,
                        output_file="[ERROR]",
                        word_count=0,
                        content_hash="",
                        extraction_mode=mode,
                        status="failure"
                    ))
            except Exception as e:
                logger.error(f"💥 Unexpected error processing {page_url}: {e}", exc_info=True)
    finally:
        # Cleanup Playwright
        if browser:
            browser.close()
        if playwright_context:
            playwright_context.stop()

    # 4. Final Aggregated Outputs
    write_chunks_manifest(all_chunks, out_path)
    
    manifest = CorpusManifest(
        run_id=str(uuid.uuid4()),
        root_url=url,
        total_pages=len([p for p in manifest_pages if p.status == "success"]),
        pages=manifest_pages
    )
    
    write_manifest(manifest, out_path)
    
    logger.info(f"Run completed. Processed {len(manifest_pages)} pages.")
    logger.info(f"Success: {len([p for p in manifest_pages if p.status == 'success'])}")
    logger.info(f"Duplicates: {len([p for p in manifest_pages if p.status == 'duplicate'])}")
    logger.info(f"Total Chunks: {len(all_chunks)}")

if __name__ == "__main__":
    app()
