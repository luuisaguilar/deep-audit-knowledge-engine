import streamlit as st
import pandas as pd
import time
import io
import zipfile
import os
from datetime import datetime
from youtube_analyzer import get_video_list, get_transcript, analyze_video_content
from github_analyzer import get_user_repos, get_repo_structure, identify_critical_files, fetch_file_content, analyze_repository_wiki
from web_analyzer import fetch_web_content, analyze_web_content
from cooking_analyzer import analyze_cooking_video
from knowledge_sync import sync_all_to_obsidian
from rss_manager import fetch_new_articles, process_rss_article
from rss_db import get_feeds, add_feed, remove_feed
from notebooklm_pack import generate_source_list, generate_context_markdown
from core.db import has_been_processed, record_ingestion, get_ingestion_stats, list_recent_ingestions
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Deep Audit Knowledge Engine",
    page_icon="🧠",
    layout="wide"
)

# --- ESTILOS PERSONALIZADOS ---
st.markdown("""
    <style>
    .stApp { background-color: #d1d5db !important; }
    .main .block-container, p, li, span, label { color: #000000 !important; font-weight: 500; }
    .stButton>button { background-color: #004a99 !important; color: #ffffff !important; border-radius: 6px; font-weight: bold; border: none; }
    .stButton>button:hover { background-color: #003366 !important; }
    h1, h2, h3 { color: #004a99 !important; font-weight: 800 !important; }
    button[kind="header"] svg, button[kind="secondary"] svg, .stDataFrame svg { fill: white !important; color: white !important; }
    .stTextInput input { background-color: #f3f4f6 !important; color: #000000 !important; }
    div[data-testid="stExpander"] { background-color: #e5e7eb !important; border: 1px solid #9ca3af; border-radius: 8px; margin-bottom: 1rem; }
    [data-testid="stSidebar"] { background-color: #e5e7eb !important; border-right: 1px solid #9ca3af; }
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN DE PERSISTENCIA ---
if 'vault_path' not in st.session_state:
    st.session_state.vault_path = os.getenv("VAULT_PATH", "/mnt/obsidian-vault")
if 'auto_save' not in st.session_state:
    st.session_state.auto_save = True

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Knowledge Engine")
    st.info("Motores: Gemini 2.0 Flash + YT + GH + Web")
    
    st.session_state.vault_path = st.text_input("📂 Ruta Obsidian Vault (Knowledge Folder)", st.session_state.vault_path)
    st.session_state.auto_save = st.checkbox("💾 Guardar automáticamente en Vault", st.session_state.auto_save)
    
    st.markdown("---")
    if st.button("🗑️ Limpiar Sesión"):
        for key in ['video_list', 'yt_audit_results', 'repo_list', 'gh_audit_results', 'web_targets', 'web_audit_results', 'transcript_cache', 'rss_articles', 'rss_results', 'chef_video_list', 'last_recipes_processed']:
            if key in st.session_state: del st.session_state[key]
        st.rerun()

def save_note(content, filename, subfolder):
    """Guarda una nota en el vault local y retorna la ruta del archivo guardado, o None."""
    if not filename.endswith(".md"): filename += ".md"
    basename, ext = os.path.splitext(filename)
    clean_base = "".join([c if c.isalnum() or c in (' ', '_', '-') else "_" for c in basename])
    clean_name = f"{clean_base}{ext}"
    
    if st.session_state.auto_save and st.session_state.vault_path:
        target_dir = os.path.join(st.session_state.vault_path, subfolder)
        os.makedirs(target_dir, exist_ok=True)
        try:
            filepath = os.path.join(target_dir, clean_name)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return filepath
        except Exception as e:
            st.error(f"Error al escribir en Vault: {e}")
    return None

# --- MAIN UI ---
st.title("🧠 Deep Audit Engine")
st.markdown("Ecosistema de Ingesta Inteligente para Obsidian.")

# Inicializar estados de datos
if 'video_list' not in st.session_state: st.session_state.video_list = []
if 'yt_audit_results' not in st.session_state: st.session_state.yt_audit_results = {}
if 'repo_list' not in st.session_state: st.session_state.repo_list = []
if 'gh_audit_results' not in st.session_state: st.session_state.gh_audit_results = {}
if 'web_targets' not in st.session_state: st.session_state.web_targets = []
if 'web_audit_results' not in st.session_state: st.session_state.web_audit_results = {}
if 'chef_video_list' not in st.session_state: st.session_state.chef_video_list = []
if 'last_recipes_processed' not in st.session_state: st.session_state.last_recipes_processed = []
if 'transcript_cache' not in st.session_state: st.session_state.transcript_cache = {}
if 'rss_articles' not in st.session_state: st.session_state.rss_articles = []
if 'rss_results' not in st.session_state: st.session_state.rss_results = {}

tabs = st.tabs(["📺 YouTube Analysis", "💻 GitHub Deep Audit", "🌐 Web Ingestion", "🍳 Digital Chef", "📰 RSS Monitor", "🧠 Obsidian Sync", "📚 NotebookLM Pack", "📊 Analytics"])

# ==========================================
# TAB 0: YOUTUBE
# ==========================================
with tabs[0]:
    col1, col2 = st.columns([3, 1])
    with col1:
        url_input = st.text_input("URL del Canal o Búsqueda", placeholder="https://www.youtube.com/@midudev", key="yt_input")
    with col2:
        st.write("")
        if st.button("🔍 Indexar Canal", key="btn_yt_index"):
            if url_input:
                with st.spinner("Indexando videos..."):
                    try:
                        vids = get_video_list(url_input, limit=20)
                        for v in vids: v['Selected'] = False
                        st.session_state.video_list = vids
                    except Exception as e:
                        st.error(f"Error: {e}")

    if st.session_state.video_list:
        st.markdown("### 📋 Selección de Videos")
        c1, c2, _ = st.columns([1,1,3])
        if c1.button("✅ Seleccionar Todos", key="sel_all_yt"):
            for row in st.session_state.video_list: row['Selected'] = True
            st.rerun()
        if c2.button("❌ Deseleccionar", key="desel_all_yt"):
            for row in st.session_state.video_list: row['Selected'] = False
            st.rerun()

        edited_yt = st.data_editor(
            pd.DataFrame(st.session_state.video_list),
            column_config={
                "Selected": st.column_config.CheckboxColumn("Auditar?", default=False),
                "url": st.column_config.LinkColumn("YouTube Link"),
                "views": st.column_config.NumberColumn("Vistas", format="%d"),
                "id": None, "description": None
            },
            disabled=["title", "date", "views", "url", "id", "description"],
            use_container_width=True, hide_index=True, key="yt_editor"
        )
        st.session_state.video_list = edited_yt.to_dict('records')
        selected_vids = [v for v in st.session_state.video_list if v.get('Selected')]
        
        if selected_vids and st.button("🚀 Iniciar Auditoría YT"):
            progress = st.progress(0)
            for idx, vid in enumerate(selected_vids):
                source_url = vid.get('url', f"https://www.youtube.com/watch?v={vid['id']}")
                if has_been_processed(source_url):
                    st.info(f"⏭️ Ya procesado: {vid['title']}")
                    progress.progress((idx + 1) / len(selected_vids))
                    continue
                with st.spinner(f"Analizando: {vid['title']}"):
                    try:
                        if vid['id'] not in st.session_state.transcript_cache:
                            st.session_state.transcript_cache[vid['id']] = get_transcript(vid['id'])
                        t, lang = st.session_state.transcript_cache[vid['id']]
                        analysis = analyze_video_content(vid, t, lang)
                        
                        if "⚠️ ERROR" not in analysis:
                            st.session_state.yt_audit_results[vid['id']] = {'title': vid['title'], 'content': analysis}
                            vault_file = save_note(analysis, f"YT_{vid['title']}", "10_YouTube")
                            record_ingestion('youtube', source_url, vid['title'], vault_path=str(vault_file) if vault_file else None)
                            st.expander(f"✅ {vid['title']}").markdown(analysis)
                        else:
                            record_ingestion('youtube', source_url, vid['title'], status='failed', error_message=analysis)
                            st.error(f"Error en {vid['title']}: {analysis}")
                    except Exception as e:
                        record_ingestion('youtube', source_url, vid['title'], status='failed', error_message=str(e))
                        st.error(f"Error en {vid['title']}: {e}")
                progress.progress((idx + 1) / len(selected_vids))

    if st.session_state.yt_audit_results:
        zip_yt = io.BytesIO()
        with zipfile.ZipFile(zip_yt, "a", zipfile.ZIP_DEFLATED, False) as zf:
            for vid_id, data in st.session_state.yt_audit_results.items():
                zf.writestr(f"{data['title']}.md", data['content'])
        st.download_button("🎁 Descargar ZIP (YouTube)", zip_yt.getvalue(), "yt_audit.zip", "application/zip")

# ==========================================
# TAB 1: GITHUB
# ==========================================
with tabs[1]:
    col3, col4 = st.columns([3, 1])
    with col3:
        user_input = st.text_input("Usuario o organización", placeholder="midudev", key="gh_input")
    with col4:
        st.write("")
        if st.button("🔎 Listar Repos", key="btn_gh_list"):
            if user_input:
                with st.spinner("Obteniendo repositorios..."):
                    try:
                        repos = get_user_repos(user_input)
                        for r in repos: r['Selected'] = False
                        st.session_state.repo_list = repos
                    except Exception as e:
                        st.error(f"Error: {e}")

    if st.session_state.repo_list:
        edited_gh = st.data_editor(
            pd.DataFrame(st.session_state.repo_list),
            column_config={
                "Selected": st.column_config.CheckboxColumn("Analizar?", default=False),
                "url": st.column_config.LinkColumn("GitHub Link"),
                "stars": st.column_config.NumberColumn("⭐ Stars"),
                "owner": None, "full_name": None
            },
            disabled=["name", "description", "language", "stars", "url", "owner", "full_name"],
            use_container_width=True, hide_index=True, key="gh_editor"
        )
        st.session_state.repo_list = edited_gh.to_dict('records')
        selected_repos = [r for r in st.session_state.repo_list if r.get('Selected')]

        if selected_repos and st.button("🧬 Iniciar Deep Audit GitHub"):
            progress_gh = st.progress(0)
            for idx, repo in enumerate(selected_repos):
                source_url = repo.get('url', f"https://github.com/{repo['full_name']}")
                if has_been_processed(source_url):
                    st.info(f"⏭️ Ya procesado: {repo['name']}")
                    progress_gh.progress((idx + 1) / len(selected_repos))
                    continue
                with st.spinner(f"Escaneando: {repo['name']}"):
                    try:
                        structure = get_repo_structure(repo['owner'], repo['name'], repo.get('default_branch', 'main'))
                        crit_files = identify_critical_files(structure)
                        files_data = {f: fetch_file_content(repo['owner'], repo['name'], f) for f in crit_files if fetch_file_content(repo['owner'], repo['name'], f)}
                        analysis_gh = analyze_repository_wiki(repo['owner'], repo['name'], repo, structure, files_data)
                        
                        if "⚠️ ERROR" not in analysis_gh:
                            st.session_state.gh_audit_results[repo['full_name']] = {'name': repo['name'], 'content': analysis_gh}
                            vault_file = save_note(analysis_gh, f"WIKI_{repo['name']}", "20_GitHub")
                            record_ingestion('github', source_url, repo['name'], vault_path=str(vault_file) if vault_file else None)
                            st.expander(f"✅ {repo['name']} Wiki").markdown(analysis_gh)
                        else:
                            record_ingestion('github', source_url, repo['name'], status='failed', error_message=analysis_gh)
                    except Exception as e:
                        record_ingestion('github', source_url, repo['name'], status='failed', error_message=str(e))
                        st.error(f"Error en {repo['name']}: {e}")
                progress_gh.progress((idx + 1) / len(selected_repos))

    if st.session_state.gh_audit_results:
        zip_gh = io.BytesIO()
        with zipfile.ZipFile(zip_gh, "a", zipfile.ZIP_DEFLATED, False) as zf_gh:
            for repo_id, data in st.session_state.gh_audit_results.items():
                zf_gh.writestr(f"WIKI_{data['name']}.md", data['content'])
        st.download_button("🎁 Descargar ZIP (GitHub)", zip_gh.getvalue(), "gh_wikis.zip", "application/zip")

# ==========================================
# TAB 2: WEB INGESTION
# ==========================================
with tabs[2]:
    st.subheader("🌐 Ingesta de Artículos y Documentación Web")
    web_url = st.text_input("Ingresa URL del artículo", placeholder="https://ejemplo.com/blog/tecnico", key="web_url_input")
    if st.button("➕ Agregar a lista"):
        if web_url and web_url not in [w['url'] for w in st.session_state.web_targets]:
            st.session_state.web_targets.append({'url': web_url, 'Selected': True})
            st.rerun()

    if st.session_state.web_targets:
        edited_web = st.data_editor(
            pd.DataFrame(st.session_state.web_targets),
            column_config={"Selected": st.column_config.CheckboxColumn("Procesar?", default=True), "url": st.column_config.LinkColumn("URL Fuente")},
            use_container_width=True, hide_index=True, key="web_editor"
        )
        st.session_state.web_targets = edited_web.to_dict('records')
        selected_web = [w for w in st.session_state.web_targets if w.get('Selected')]

        if selected_web and st.button("⚡ Procesar Artículos Web"):
            prog_web = st.progress(0)
            for idx, item in enumerate(selected_web):
                if has_been_processed(item['url']):
                    st.info(f"⏭️ Ya procesado: {item['url']}")
                    prog_web.progress((idx+1)/len(selected_web))
                    continue
                with st.spinner(f"Crawling: {item['url']}"):
                    try:
                        web_data = fetch_web_content(item['url'])
                        analysis = analyze_web_content(web_data)
                        if "⚠️ ERROR" not in analysis:
                            title = web_data.get('title', 'Web_Note')
                            st.session_state.web_audit_results[item['url']] = {'title': title, 'content': analysis}
                            vault_file = save_note(analysis, f"WEB_{title}", "30_Web")
                            record_ingestion('web', item['url'], title, vault_path=str(vault_file) if vault_file else None)
                            st.expander(f"✅ {title}").markdown(analysis)
                        else:
                            record_ingestion('web', item['url'], status='failed', error_message=analysis)
                    except Exception as e:
                        record_ingestion('web', item['url'], status='failed', error_message=str(e))
                        st.error(f"Error: {e}")
                prog_web.progress((idx+1)/len(selected_web))

    if st.session_state.web_audit_results:
        zip_web = io.BytesIO()
        with zipfile.ZipFile(zip_web, "a", zipfile.ZIP_DEFLATED, False) as zf_w:
            for url, data in st.session_state.web_audit_results.items():
                zf_w.writestr(f"WEB_{data['title']}.md", data['content'])
        st.download_button("🎁 Descargar ZIP (Web)", zip_web.getvalue(), "web_audit.zip", "application/zip")

# ==========================================
# TAB 3: DIGITAL CHEF
# ==========================================
with tabs[3]:
    st.subheader("🍳 Chef Inteligente")
    chef_url = st.text_input("URL Canal Cocina", key="chef_url_input")
    if st.button("🔍 Indexar Cocina"):
        if chef_url:
            vids = get_video_list(chef_url, limit=10)
            for v in vids: v['Selected'] = False
            st.session_state.chef_video_list = vids

    if st.session_state.chef_video_list:
        edited_chef = st.data_editor(
            pd.DataFrame(st.session_state.chef_video_list),
            column_config={"Selected": st.column_config.CheckboxColumn("¿Receta?", default=False), "url": st.column_config.LinkColumn("Link"), "id": None, "description": None, "views": None, "date": None},
            disabled=["title", "url"], use_container_width=True, hide_index=True, key="chef_editor"
        )
        st.session_state.chef_video_list = edited_chef.to_dict('records')
        selected_chef = [v for v in st.session_state.chef_video_list if v.get('Selected')]

        if selected_chef and st.button("🧑‍🍳 Generar Recetas"):
            st.session_state.last_recipes_processed = []
            for vid in selected_chef:
                with st.spinner(f"Cocinando: {vid['title']}"):
                    t, lang = get_transcript(vid['id'])
                    vid['transcript'] = t
                    recipe = analyze_cooking_video(vid)
                    if "⚠️ ERROR" not in recipe:
                        st.session_state.last_recipes_processed.append(recipe)
                        save_note(recipe, f"Receta_{vid['title']}", "50_Recetas")
                        st.expander(f"✅ {vid['title']}").markdown(recipe)

# ==========================================
# TAB 4: RSS MONITOR
# ==========================================
with tabs[4]:
    st.subheader("📰 Monitoreo de Feeds RSS")
    col_r1, col_r2 = st.columns([2, 1])
    with col_r2:
        st.markdown("### ⚙️ Gestión de Feeds")
        n_name = st.text_input("Nombre Feed")
        n_url = st.text_input("URL Feed")
        if st.button("➕ Añadir"):
            if n_name and n_url: add_feed(n_url, n_name); st.rerun()
        feeds = get_feeds()
        if feeds:
            f_del = st.selectbox("Eliminar", [f"{f[2]} ({f[1]})" for f in feeds])
            if st.button("🗑️ Eliminar"):
                f_obj = [f for f in feeds if f"{f[2]} ({f[1]})" == f_del][0]
                remove_feed(f_obj[0]); st.rerun()

    with col_r1:
        if st.button("🔄 Buscar Artículos"):
            st.session_state.rss_articles = fetch_new_articles()
        if st.session_state.rss_articles:
            edited_rss = st.data_editor(
                pd.DataFrame(st.session_state.rss_articles),
                column_config={"Selected": st.column_config.CheckboxColumn("Procesar?", default=True), "link": st.column_config.LinkColumn("Link"), "feed_id": None},
                use_container_width=True, hide_index=True, key="rss_editor"
            )
            st.session_state.rss_articles = edited_rss.to_dict('records')
            if st.button("🚀 Procesar RSS"):
                for art in [a for a in st.session_state.rss_articles if a.get('Selected')]:
                    analysis = process_rss_article(art)
                    if "⚠️ ERROR" not in analysis:
                        st.session_state.rss_results[art['link']] = {'title': art['title'], 'content': analysis}
                        save_note(analysis, f"RSS_{art['title']}", os.path.join("30_Web", "RSS"))
                        st.expander(f"✅ {art['title']}").markdown(analysis)

# ==========================================
# TAB 5: OBSIDIAN SYNC
# ==========================================
with tabs[5]:
    st.subheader("🧠 Obsidian Knowledge Sync")
    if st.button("🔄 Sincronizar Ahora"):
        with st.spinner("Sincronizando agentes..."):
            msg = sync_all_to_obsidian(st.session_state.vault_path)
            st.success(msg)

# ==========================================
# TAB 6: NOTEBOOKLM PACK
# ==========================================
with tabs[6]:
    st.header("📚 NotebookLM Source Pack")
    all_sources = []
    if st.session_state.yt_audit_results:
        for vid_id, data in st.session_state.yt_audit_results.items():
            all_sources.append({"Tipo": "YouTube", "Nombre": data['title'], "Link": f"https://www.youtube.com/watch?v={vid_id}"})
    if st.session_state.gh_audit_results:
        for repo_name, data in st.session_state.gh_audit_results.items():
            all_sources.append({"Tipo": "GitHub", "Nombre": repo_name, "Link": f"https://github.com/{repo_name}"})
    if st.session_state.web_audit_results:
        for url, data in st.session_state.web_audit_results.items():
            all_sources.append({"Tipo": "Web", "Nombre": data['title'], "Link": url})
    if st.session_state.rss_results:
        for link, data in st.session_state.rss_results.items():
            all_sources.append({"Tipo": "RSS", "Nombre": data['title'], "Link": link})

    if all_sources:
        st.table(pd.DataFrame(all_sources))
        c1, c2 = st.columns(2)
        if c1.button("📄 Generar Lista URLs"):
            urls_txt = generate_source_list(st.session_state.yt_audit_results, st.session_state.gh_audit_results, st.session_state.web_audit_results, st.session_state.rss_results)
            st.download_button("⬇️ Descargar URLs", urls_txt, "sources.txt")
        if c2.button("📝 Generar Contexto Maestro"):
            ctx_md = generate_context_markdown(st.session_state.yt_audit_results, st.session_state.gh_audit_results, st.session_state.web_audit_results, st.session_state.rss_results)
            save_note(ctx_md, f"NotebookLM_Context_{datetime.now().strftime('%Y%m%d')}", "40_NotebookLM")
            st.download_button("⬇️ Descargar Contexto", ctx_md, "context.md")
    else:
        st.warning("No hay fuentes procesadas en esta sesión.")

# ==========================================
# TAB 7: ANALYTICS
# ==========================================
with tabs[7]:
    st.header("📊 Knowledge Engine Analytics")
    st.markdown("Estadísticas globales de todas las ingestas registradas en `knowledge.db`.")

    stats = get_ingestion_stats()

    # --- KPI cards ---
    k1, k2, k3 = st.columns(3)
    k1.metric("Total Ingestas", stats["total"])
    k2.metric("✅ Exitosas", stats["success"])
    k3.metric("❌ Fallidas", stats["failed"])

    st.divider()

    # --- By source type ---
    if stats["by_type"]:
        st.subheader("📂 Ingestas por Tipo de Fuente")
        type_df = pd.DataFrame(stats["by_type"], columns=["Fuente", "Cantidad"])
        st.bar_chart(type_df.set_index("Fuente"))

    # --- Timeline ---
    if stats["by_date"]:
        st.subheader("📅 Timeline de Procesamiento (últimos 30 días)")
        date_df = pd.DataFrame(stats["by_date"], columns=["Fecha", "Cantidad"])
        date_df = date_df.sort_values("Fecha")
        st.line_chart(date_df.set_index("Fecha"))

    st.divider()

    # --- Recent items table ---
    if stats["recent"]:
        st.subheader("🕐 Últimas 10 Ingestas")
        recent_df = pd.DataFrame(stats["recent"])
        display_cols = ["source_type", "title", "source_url", "status", "processed_at"]
        available_cols = [c for c in display_cols if c in recent_df.columns]
        st.dataframe(
            recent_df[available_cols].rename(columns={
                "source_type": "Tipo",
                "title": "Título",
                "source_url": "URL",
                "status": "Estado",
                "processed_at": "Procesado",
            }),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Aún no hay ingestas registradas. Procesa contenido desde cualquier tab para ver estadísticas aquí.")

    # --- Full history download ---
    all_ingestions = list_recent_ingestions(limit=500)
    if all_ingestions:
        csv_data = pd.DataFrame(all_ingestions).to_csv(index=False)
        st.download_button("📥 Exportar historial completo (CSV)", csv_data, "ingestion_history.csv", "text/csv")
