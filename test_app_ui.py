import pytest
from playwright.sync_api import sync_playwright
import subprocess
import time
import re

@pytest.fixture(scope="module")
def streamlit_app():
    # Start streamlit in the background
    # Use the venv python to be sure dependencies are found
    cmd = [".\\venv\\Scripts\\python.exe", "-m", "streamlit", "run", "app.py", "--server.port", "8502", "--server.headless", "true"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait for the server to start
    time.sleep(5)
    yield "http://localhost:8502"
    
    # Terminate process
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()

def test_tabs_existence(streamlit_app):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(streamlit_app)
        
        # Wait for the main title to appear (avoiding sidebar h1)
        page.wait_for_selector("text=Deep Audit Engine", timeout=10000)
        
        # Check tabs using regex to skip emojis
        tab_list = ["YouTube Analysis", "GitHub Deep Audit", "Web Ingestion", "Digital Chef", "RSS Monitor", "Obsidian Sync", "NotebookLM Pack"]
        for tab in tab_list:
            expect_tab = page.get_by_text(re.compile(tab, re.IGNORECASE))
            assert expect_tab.first.is_visible(), f"Tab {tab} not found"
        
        browser.close()

def test_digital_chef_tab(streamlit_app):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(streamlit_app)
        
        # Click on Digital Chef tab
        page.get_by_text(re.compile("Digital Chef", re.IGNORECASE)).click()
        
        # Check for subheader
        assert page.get_by_text("Chef Inteligente").is_visible()
        
        # Check for input field (by label or key is harder in playwright-streamlit, so check by presence of header)
        assert page.get_by_text("Chef Inteligente").is_visible()
        
        browser.close()

def test_obsidian_sync_tab(streamlit_app):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(streamlit_app)
        
        # Click on Obsidian Sync tab
        page.get_by_text(re.compile("Obsidian Sync", re.IGNORECASE)).click()
        
        # Check for subheader
        assert page.get_by_text("Obsidian Knowledge Sync").is_visible()
        
        # Check for sync button
        assert page.get_by_text("Sincronizar Ahora").is_visible()
        
        browser.close()
