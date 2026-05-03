
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

url = "https://www.builderbot.app/en"
response = requests.get(url)
soup = BeautifulSoup(response.text, "lxml")

SIDEBAR_SELECTORS = [
    "nav", "aside", "[role='navigation']", "#sidebar", ".sidebar", 
    ".navigation", ".menu", ".docs-sidebar", ".docs-nav", ".td-sidebar", 
    "#toc", ".toc", ".sidebar-container", ".sidebar-nav", ".lg\\:w-72", 
    ".lg\\:w-64", "div.contents"
]

print(f"Checking {url}...")
sidebar = None
for selector in SIDEBAR_SELECTORS:
    # Use backslashes correctly for CSS selector with colons
    clean_selector = selector.replace("\\", "") # BeautifulSoup select handles colons differently if literal
    try:
        # For BS4, colons in classes need to be escaped or used via attribute selector
        if ":" in selector:
             # Convert .lg:w-72 to [class*='lg:w-72'] or similar
             attr_selector = f"[class*='{selector.strip('.').replace('\\', '')}']"
             candidate = soup.select_one(attr_selector)
        else:
             candidate = soup.select_one(selector)
             
        if candidate:
            links = candidate.find_all("a", href=True)
            if links:
                print(f"MATCH: {selector} found {len(links)} links")
                for l in links[:5]:
                    print(f"  - {l.text.strip()}: {l['href']}")
                sidebar = candidate
                break
    except Exception as e:
        print(f"Err with {selector}: {e}")

if not sidebar:
    print("NO SIDEBAR MATCHED. Falling back to <li>...")
    li_links = soup.find_all("li")
    print(f"Found {len(li_links)} <li> elements")
