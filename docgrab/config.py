from pathlib import Path
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

class Config(BaseModel):
    """
    Core configuration for a DocGrab run.
    """
    root_url: str = Field(..., description="The base URL of the documentation to extract")
    output_dir: Path = Field(default=Path("./exports"), description="Where to save the outputs")
    user_agent: str = Field(
        default="DocGrab/0.1 (+https://github.com/docgrab)",
        description="User-Agent string for HTTP requests"
    )
    request_timeout: int = Field(default=30, description="Timeout in seconds for requests")
    max_retries: int = Field(default=3, description="Maximum number of retries for failed requests")
    
    # Playwright Settings
    playwright_enabled: bool = Field(default=True, description="Whether to use Playwright for rendered extraction")
    browser_timeout: int = Field(default=30000, description="Timeout in ms for browser operations")
    wait_selectors: list[str] = Field(default_factory=list, description="Selectors to wait for before extraction")
    fallback_threshold: float = Field(default=0.5, description="Score threshold to trigger Playwright fallback")
    page_load_timeout: int = Field(default=60000, description="Timeout in ms for page load")

    # Run ID for directory isolation
    run_id: Optional[str] = None
