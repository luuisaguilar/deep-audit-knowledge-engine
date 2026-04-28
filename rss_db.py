import sqlite3
import os

DB_PATH = "rss_feeds.db"

def init_db():
    """Inicializa la base de datos y crea las tablas si no existen."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabla de Feeds
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            categoria TEXT DEFAULT 'General'
        )
    ''')
    
    # Tabla de Artículos procesados/vistos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feed_id INTEGER,
            link TEXT UNIQUE NOT NULL,
            title TEXT,
            published TEXT,
            status TEXT DEFAULT 'new',
            FOREIGN KEY (feed_id) REFERENCES feeds (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_feed(url, nombre, categoria="General"):
    """Agrega un nuevo feed a la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO feeds (url, nombre, categoria) VALUES (?, ?, ?)", (url, nombre, categoria))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_feeds():
    """Retorna todos los feeds registrados."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, url, nombre, categoria FROM feeds")
    feeds = cursor.fetchall()
    conn.close()
    return feeds

def remove_feed(feed_id):
    """Elimina un feed y sus artículos asociados."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM articles WHERE feed_id = ?", (feed_id,))
    cursor.execute("DELETE FROM feeds WHERE id = ?", (feed_id,))
    conn.commit()
    conn.close()

def add_article(feed_id, link, title, published):
    """Registra un artículo como visto."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO articles (feed_id, link, title, published) VALUES (?, ?, ?, ?)", 
                       (feed_id, link, title, published))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def is_article_seen(link):
    """Verifica si un artículo ya existe en la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM articles WHERE link = ?", (link,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def mark_as_processed(link):
    """Marca un artículo como procesado."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE articles SET status = 'processed' WHERE link = ?", (link,))
    conn.commit()
    conn.close()

def get_all_processed_articles():
    """Retorna todos los artículos marcados como procesados."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT link, title, published FROM articles WHERE status = 'processed'")
    articles = cursor.fetchall()
    conn.close()
    return articles

# Inicializar al importar
init_db()
