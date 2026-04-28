import os
from datetime import datetime
from rss_db import get_all_processed_articles
from knowledge_sync import get_auctionbot_summary, get_dexscreener_summary

def generate_source_list(yt_results, gh_results, web_results, rss_results):
    """
    Genera una lista de URLs de todas las fuentes procesadas.
    session_results: dict con los resultados de la sesión actual.
    """
    urls = []
    
    # YouTube
    for vid_id, data in yt_results.items():
        # Buscamos la URL original en el objeto de datos si estuviera, 
        # pero streamlit solo guarda el contenido. Asumiremos que la URL se puede reconstruir o se pasa.
        # Por simplicidad, reconstruct
        urls.append(f"https://www.youtube.com/watch?v={vid_id}")
        
    # GitHub
    for repo_full_name in gh_results.keys():
        urls.append(f"https://github.com/{repo_full_name}")
        
    # Web
    for url in web_results.keys():
        urls.append(url)
        
    # RSS (del diccionario de la sesión)
    for link in rss_results.keys():
        urls.append(link)
        
    # RSS Históricos (opcional para el pack completo)
    historical_rss = get_all_processed_articles()
    for link, title, published in historical_rss:
        if link not in urls:
            urls.append(link)
            
    return "\n".join(set(urls))

def generate_context_markdown(yt_results, gh_results, web_results, rss_results, include_sync=True):
    """
    Genera una nota maestra con todos los resúmenes de la sesión.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    md = [
        "---",
        "tipo: notebooklm_source_pack",
        f"fecha_generacion: {now}",
        "objetivo: contexto_maestro_investigacion",
        "---",
        "",
        "# 📚 NotebookLM Context Pack",
        "Este documento contiene el resumen y análisis de todas las fuentes procesadas en esta investigación técnica.",
        ""
    ]
    
    # YouTube
    if yt_results:
        md.append("## 📺 YouTube Audits")
        for data in yt_results.values():
            md.append(f"### {data['title']}")
            md.append(data['content'])
            md.append("")
            
    # GitHub
    if gh_results:
        md.append("## 💻 GitHub Wikis")
        for data in gh_results.values():
            md.append(f"### Repo: {data['name']}")
            md.append(data['content'])
            md.append("")
            
    # Web & RSS
    if web_results or rss_results:
        md.append("## 🌐 Web & RSS Insights")
        for data in list(web_results.values()) + list(rss_results.values()):
            md.append(f"### {data['title']}")
            md.append(data['content'])
            md.append("")
            
    # Obsidian Sync / Agentes Externos
    if include_sync:
        md.append("## 🤖 External Agent Sync (Obsidian Sync)")
        md.append("### AuctionBot Summary")
        md.append(get_auctionbot_summary())
        md.append("")
        md.append("### DexScreener Summary")
        md.append(get_dexscreener_summary())
        md.append("")

    return "\n".join(md)
