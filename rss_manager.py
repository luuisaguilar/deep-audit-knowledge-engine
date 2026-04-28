import feedparser
import ssl
from rss_db import add_feed, get_feeds, add_article, is_article_seen, mark_as_processed
from web_analyzer import fetch_web_content, analyze_web_content

# Evitar errores de certificado SSL en algunos sistemas
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

DEFAULT_FEEDS = [
    ("https://news.ycombinator.com/rss", "Hacker News", "General"),
    ("https://aws.amazon.com/blogs/aws/feed/", "AWS Machine Learning", "AI/Cloud"),
    ("https://openrss.org/openai.com/blog", "OpenAI Blog", "AI"),
    ("https://blog.google/rss/", "Google The Keyword", "AI/General"),
    ("https://research.google/blog/feed/", "Google Research", "AI/Scientific"),
    ("https://blogs.microsoft.com/ai/feed/", "Microsoft AI", "AI"),
]

def load_default_feeds():
    """Carga los feeds por defecto si la base de datos está vacía."""
    current_feeds = get_feeds()
    if not current_feeds:
        for url, nombre, cat in DEFAULT_FEEDS:
            add_feed(url, nombre, cat)

def fetch_new_articles():
    """Busca artículos nuevos en todos los feeds registrados."""
    feeds = get_feeds()
    new_articles = []
    
    for f_id, url, nombre, cat in feeds:
        try:
            d = feedparser.parse(url)
            for entry in d.entries:
                link = entry.link
                title = entry.title
                published = entry.get('published', entry.get('updated', 'N/A'))
                
                if not is_article_seen(link):
                    # Solo agregamos a la lista, el registro en DB se hace al mostrar o procesar
                    new_articles.append({
                        'feed_id': f_id,
                        'feed_name': nombre,
                        'title': title,
                        'link': link,
                        'published': published,
                        'category': cat
                    })
        except Exception as e:
            print(f"Error parseando feed {nombre}: {e}")
            
    return new_articles

def process_rss_article(article_data):
    """Descarga, analiza y marca como procesado un artículo de RSS."""
    # 1. Fetch content
    content_data = fetch_web_content(article_data['link'])
    
    # 2. Analyze
    if 'error' not in content_data:
        analysis = analyze_web_content(content_data)
        
        # 3. Mark as seen in DB so it doesn't appear again
        add_article(
            article_data['feed_id'],
            article_data['link'],
            article_data['title'],
            article_data['published']
        )
        mark_as_processed(article_data['link'])
        
        return analysis
    else:
        return f"⚠️ Error al obtener contenido: {content_data['error']}"

# Cargar feeds al iniciar el módulo
load_default_feeds()
