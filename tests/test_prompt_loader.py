import os
import pytest
from core.prompt_loader import render_prompt

def test_render_prompt():
    """Test that Jinja2 correctly injects variables into a markdown template."""
    # We create a dummy template in the prompts dir temporarily or use an existing one
    # Assuming audio_analysis.md exists and has {{ title }}
    context = {
        "title": "Test Title 123",
        "tags": "test_tag",
        "source_url": "http://test.com",
        "date": "2024-01-01"
    }
    result = render_prompt("audio_analysis", context)
    
    assert "Test Title 123" in result
    assert "test_tag" in result
    assert "http://test.com" in result
    assert "2024-01-01" in result
    assert "{{ title }}" not in result # Ensure variable was actually replaced
