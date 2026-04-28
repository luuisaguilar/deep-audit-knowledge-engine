"""Prompt template loader for the Deep Audit Knowledge Engine.

Loads Markdown prompt templates from the ``prompts/`` directory and renders
them using Jinja2 (already bundled with Streamlit).  Templates use the
standard ``{{ variable }}`` syntax.

Usage::

    from core.prompt_loader import render_prompt

    prompt = render_prompt("youtube_analysis", {
        "title": video["title"],
        "url": video["url"],
        "content": transcript_text,
        ...
    })
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

_env = Environment(
    loader=FileSystemLoader(str(_PROMPTS_DIR)),
    # Keep undefined variables visible so we can debug easily
    undefined=__import__("jinja2").DebugUndefined,
    # Don't auto-escape — we're building plain-text prompts, not HTML
    autoescape=False,
)


def render_prompt(template_name: str, variables: dict) -> str:
    """Render a prompt template with the given variables.

    Args:
        template_name: Filename without extension (e.g. ``"youtube_analysis"``).
                       The ``.md`` suffix is appended automatically.
        variables: Dict of values to inject into the template.

    Returns:
        The fully rendered prompt string.

    Raises:
        FileNotFoundError: If the template file does not exist.
    """
    filename = f"{template_name}.md"
    try:
        template = _env.get_template(filename)
    except TemplateNotFound:
        raise FileNotFoundError(
            f"Prompt template '{filename}' not found in {_PROMPTS_DIR}"
        )
    return template.render(**variables)


def list_templates() -> list[str]:
    """Return a sorted list of available template basenames."""
    return sorted(p.stem for p in _PROMPTS_DIR.glob("*.md") if not p.name.startswith("_"))
