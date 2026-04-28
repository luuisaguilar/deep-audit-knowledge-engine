import requests
import datetime
from bs4 import BeautifulSoup
from config import generate_with_retry


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

    prompt = (
        "Actúa como un Curador de Conocimiento Senior y experto en Zettelkasten.\n"
        "Analiza el siguiente texto de un sitio web y genera una nota estructurada para Obsidian.\n\n"
        "REQUISITO CRÍTICO: Comienza SIEMPRE con el bloque YAML exactamente así:\n"
        "---\n"
        "tipo: web_research\n"
        f"fuente: \"{data['url']}\"\n"
        f"fecha_ingesta: {today}\n"
        "categoria: investigacion\n"
        "estado: procesado\n"
        "---\n\n"
        f"# {data['title']}\n\n"
        "Analiza el contenido. Si el idioma original es español, redacta en ESPAÑOL. De lo contrario, en INGLÉS.\n\n"
        "SECCIONES REQUERIDAS:\n"
        "1. **Resumen Ejecutivo**: Las 3 ideas más potentes del artículo.\n"
        "2. **Conceptos Técnicos**: Definiciones o herramientas mencionadas.\n"
        "3. **Análisis de Valor**: ¿Por qué es importante este contenido para un CTO/Arquitecto?\n"
        "4. **Action Items / Siguientes Pasos**: Sugerencias basadas en la lectura.\n\n"
        f"CONTENIDO WEB:\n{data['content']}"
    )

    return generate_with_retry(prompt)
