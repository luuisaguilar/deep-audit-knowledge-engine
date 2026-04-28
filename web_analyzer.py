import requests
import datetime
from bs4 import BeautifulSoup
from config import generate_with_retry
from core.prompt_loader import render_prompt


def fetch_web_content(url):
    """Extrae el texto relevante de una URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()

        title = soup.title.string if soup.title else "Sin Título"
        text = soup.get_text(separator=' ', strip=True)
        text = ' '.join(text.split())

        return {
            'title': title.strip(),
            'content': text[:15000],
            'url': url
        }
    except Exception as e:
        return {'error': str(e)}


def analyze_web_content(data):
    """Genera una nota de Obsidian con YAML a partir del contenido web."""
    if 'error' in data:
        return f"⚠️ ERROR de Conexión: {data['error']}"

    today = datetime.date.today().isoformat()

    prompt = render_prompt("web_curation", {
        "url": data['url'],
        "title": data.get('title', 'Sin Título'),
        "date": today,
        "content": data['content'],
    })

    return generate_with_retry(prompt)
