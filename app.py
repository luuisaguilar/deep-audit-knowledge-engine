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
from audio_analyzer import analyze_audio
from knowledge_sync import sync_all_to_obsidian
from rss_manager import fetch_new_articles, process_rss_article
from rss_db import get_feeds, add_feed, remove_feed
from notebooklm_pack import generate_source_list, generate_context_markdown
from core.db import (
    record_ingestion, get_ingestion_stats, list_recent_ingestions, has_been_processed,
    login_user, signup_user, logout_user, get_current_user, reset_password_user
)
from config import token_tracker
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Deep Audit Knowledge Engine",
    page_icon="🧠",
    layout="wide"
)

# --- ESTILOS PERSONALIZADOS (PREMIUM DARK MODE) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');

    :root {
        --bg-color: #0e1117;
        --secondary-bg: #161b22;
        --accent-color: #10b981;
        --text-primary: #ffffff;
        --text-secondary: #8b949e;
        --card-bg: rgba(22, 27, 34, 0.7);
    }

    /* Hide Streamlit Header & Footer */
    header[data-testid="stHeader"] { visibility: hidden; height: 0; }
    footer { visibility: hidden; }
    
    /* Remove padding at the top of the main container */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }

    .stApp { 
        background-color: var(--bg-color) !important; 
        font-family: 'Inter', sans-serif !important;
    }

    /* Sidebar Glassmorphism */
    [data-testid="stSidebar"] {
        background-color: rgba(22, 27, 34, 0.95) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px);
    }

    /* Headers */
    h1, h2, h3 { 
        color: var(--accent-color) !important; 
        font-family: 'Inter', sans-serif !important;
        font-weight: 800 !important;
        letter-spacing: -1px;
    }

    /* Text elements */
    .main .block-container, p, li, span, label, div { 
        color: var(--text-primary) !important; 
    }
    
    .stMarkdown p {
        color: var(--text-secondary) !important;
        font-weight: 400;
    }

    /* Buttons */
    .stButton>button { 
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important; 
        color: #ffffff !important; 
        border-radius: 8px !important; 
        font-weight: 700 !important; 
        border: none !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2);
        width: 100%;
    }
    .stButton>button:hover { 
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
    }

    /* Inputs */
    .stTextInput input, .stTextArea textarea { 
        background-color: var(--secondary-bg) !important; 
        color: var(--text-primary) !important; 
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
    }

    /* Cards / Containers */
    div[data-testid="stExpander"] { 
        background-color: var(--card-bg) !important; 
        border: 1px solid rgba(255, 255, 255, 0.1) !important; 
        border-radius: 12px !important; 
        margin-bottom: 1rem !important; 
        backdrop-filter: blur(5px);
    }

    /* Stats Cards Custom HTML */
    .metric-card {
        background: var(--card-bg);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: scale(1.02);
        border-color: var(--accent-color);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: var(--accent-color);
        margin: 5px 0;
    }
    .metric-label {
        color: var(--text-secondary);
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: var(--secondary-bg);
        border-radius: 8px 8px 0 0;
        padding: 0 20px;
        color: var(--text-secondary);
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--accent-color) !important;
        color: var(--bg-color) !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: var(--bg-color); }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #555; }
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN DE PERSISTENCIA ---
if 'vault_path' not in st.session_state:
    st.session_state.vault_path = os.getenv("VAULT_PATH", "/mnt/obsidian-vault")
if 'auto_save' not in st.session_state:
    st.session_state.auto_save = True

# --- AUTH SESSION MANAGEMENT ---
if 'user' not in st.session_state:
    st.session_state.user = None

# --- MODO DEV: bypass auth si Supabase no está configurado ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DEV_MODE = not (SUPABASE_URL and SUPABASE_KEY)

if DEV_MODE and not st.session_state.user:
    # Auto-login con usuario local de desarrollo
    class DevUser:
        id = "dev-user-local"
        email = "dev@local.mode"
    st.session_state.user = DevUser()
    st.session_state._dev_mode_active = True

# --- RATE LIMITING ---
def check_rate_limit(action_key, max_requests=5, window=60):
    now = time.time()
    if 'rate_limits' not in st.session_state:
        st.session_state.rate_limits = {}
    if action_key not in st.session_state.rate_limits:
        st.session_state.rate_limits[action_key] = []
    
    # Filtrar peticiones fuera de la ventana de tiempo
    st.session_state.rate_limits[action_key] = [t for t in st.session_state.rate_limits[action_key] if now - t < window]
    
    if len(st.session_state.rate_limits[action_key]) >= max_requests:
        return False
    
    st.session_state.rate_limits[action_key].append(now)
    return True

def login_screen():
    st.markdown("<h1 style='text-align: center; color: #10b981; margin-top: 50px;'>🔐 DEEP AUDIT ACCESS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8b949e;'>Ingresa al centro de comando de inteligencia</p>", unsafe_allow_html=True)
    
    # Centrar el contenedor de auth
    _, center_col, _ = st.columns([1, 2, 1])
    
    with center_col:
        auth_tab1, auth_tab2, auth_tab3 = st.tabs(["🚀 Iniciar Sesión", "📝 Registrarse", "🔑 Recuperar"])
        
        with auth_tab1:
            l_email = st.text_input("Email", key="l_email_p")
            l_pass = st.text_input("Password", type="password", key="l_pass_p")
            if st.button("ENTRAR AL ENGINE", use_container_width=True):
                if not check_rate_limit("login"):
                    st.error("Demasiados intentos. Espera un minuto.")
                else:
                    try:
                        res = login_user(l_email, l_pass)
                        st.session_state.user = res.user
                        st.rerun()
                    except Exception as e:
                        st.error(f"Acceso denegado: {e}")
                        
        with auth_tab2:
            st.info("Crea una cuenta para empezar a auditar.")
            s_email = st.text_input("Email", key="s_email_p")
            s_pass = st.text_input("Password", type="password", key="s_pass_p")
            if st.button("CREAR CUENTA MAESTRA", use_container_width=True):
                if not check_rate_limit("signup"):
                    st.error("Espera un momento antes de intentar de nuevo.")
                else:
                    try:
                        signup_user(s_email, s_pass)
                        st.success("¡Cuenta creada! Revisa tu correo de confirmación.")
                    except Exception as e:
                        st.error(f"Error en registro: {e}")
        
        with auth_tab3:
            st.write("Te enviaremos un link para resetear tu contraseña.")
            r_email = st.text_input("Email", key="r_email_p")
            if st.button("ENVIAR LINK DE RECUPERACIÓN", use_container_width=True):
                if not check_rate_limit("reset"):
                    st.error("Límite de envíos alcanzado. Revisa tu correo.")
                else:
                    try:
                        reset_password_user(r_email)
                        st.success("Si el email existe en nuestra base, recibirás un link pronto.")
                    except Exception as e:
                        st.error(f"Error: {e}")
    st.stop()

if not DEV_MODE and not st.session_state.user:
    login_screen()

# Obtener user_id para filtrar datos
user_id = st.session_state.user.id

# --- SIDEBAR ---
with st.sidebar:
    if DEV_MODE:
        st.warning("🛠️ MODO DEV ACTIVO")
        st.caption("Sin Supabase. Configura `SUPABASE_URL` y `SUPABASE_KEY` en `.env` para activar auth multi-usuario.")
    else:
        st.markdown(f"<p style='color: #8b949e;'>Conectado como: <b>{st.session_state.user.email}</b></p>", unsafe_allow_html=True)
        if st.button("🚪 Cerrar Sesión"):
            logout_user()
            st.session_state.user = None
            st.rerun()
    st.markdown("---")
    st.title("⚙️ Knowledge Engine")
    st.info("Motores: Gemini 2.0 Flash + YT + GH + Web")
    
    st.session_state.vault_path = st.text_input("📂 Ruta Obsidian Vault (Knowledge Folder)", st.session_state.vault_path)
    st.session_state.auto_save = st.checkbox("💾 Guardar automáticamente en Vault", st.session_state.auto_save)
    st.session_state.force_reprocess = st.checkbox("🔄 Forzar Re-proceso (Ignorar Dedup)", False)
    
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
        # Aislamiento por usuario
        user_id = st.session_state.user.id
        target_dir = os.path.join(st.session_state.vault_path, "users", user_id, subfolder)
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
st.markdown("<h1 style='text-align: center; font-size: 4rem; margin-bottom: 0;'>🧠 DEEP AUDIT</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #8b949e !important;'>Autonomous Knowledge Engine & Semantic Intelligence</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

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
if 'dg_discovered_links' not in st.session_state: st.session_state.dg_discovered_links = []

tab0, tab1, tab2, tab_dg, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "📺 YouTube", "💻 GitHub", "🌐 Web", "🕷️ DocGrab", "🍳 Chef", "📰 RSS", "🎙️ Audio", "🔍 Buscador", "📊 Analytics", "🧠 Obsidian Sync", "📚 NotebookLM", "---"
])

# ==========================================
# TAB 0: YOUTUBE
# ==========================================
with tab0:
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
                if not st.session_state.force_reprocess and has_been_processed(source_url, user_id=user_id):
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
                            p_tok, c_tok = token_tracker.get_and_reset()
                            record_ingestion('youtube', source_url, vid['title'], user_id=user_id, vault_path=str(vault_file) if vault_file else None, prompt_tokens=p_tok, completion_tokens=c_tok)
                            if vault_file:
                                index_document(str(vault_file), vid['title'], analysis)
                            st.expander(f"✅ {vid['title']}").markdown(analysis)
                        else:
                            p_tok, c_tok = token_tracker.get_and_reset()
                            record_ingestion('youtube', source_url, vid['title'], user_id=user_id, status='failed', error_message=analysis, prompt_tokens=p_tok, completion_tokens=c_tok)
                            st.error(f"Error en {vid['title']}: {analysis}")
                    except Exception as e:
                        p_tok, c_tok = token_tracker.get_and_reset()
                        record_ingestion('youtube', source_url, vid['title'], user_id=user_id, status='failed', error_message=str(e), prompt_tokens=p_tok, completion_tokens=c_tok)
                        st.error(f"Error en {vid['title']}: {e}")
                progress.progress((idx + 1) / len(selected_vids))

# ==========================================
# TAB 1: GITHUB
# ==========================================
with tab1:
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
                if not st.session_state.force_reprocess and has_been_processed(source_url, user_id=user_id):
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
                            p_tok, c_tok = token_tracker.get_and_reset()
                            record_ingestion('github', source_url, repo['name'], user_id=user_id, vault_path=str(vault_file) if vault_file else None, prompt_tokens=p_tok, completion_tokens=c_tok)
                            if vault_file:
                                index_document(str(vault_file), repo['name'], analysis_gh)
                            st.expander(f"✅ {repo['name']} Wiki").markdown(analysis_gh)
                        else:
                            p_tok, c_tok = token_tracker.get_and_reset()
                            record_ingestion('github', source_url, repo['name'], user_id=user_id, status='failed', error_message=analysis_gh, prompt_tokens=p_tok, completion_tokens=c_tok)
                    except Exception as e:
                        p_tok, c_tok = token_tracker.get_and_reset()
                        record_ingestion('github', source_url, repo['name'], user_id=user_id, status='failed', error_message=str(e), prompt_tokens=p_tok, completion_tokens=c_tok)
                        st.error(f"Error en {repo['name']}: {e}")
                progress_gh.progress((idx + 1) / len(selected_repos))

# ==========================================
# TAB 2: WEB
# ==========================================
with tab2:
    st.subheader("🌐 Ingesta de Artículos Web")
    web_url = st.text_input("Ingresa URL", key="web_url_input")
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

        if selected_web and st.button("⚡ Procesar Artículos Web", use_container_width=True):
            prog_web = st.progress(0)
            for idx, item in enumerate(selected_web):
                if not st.session_state.force_reprocess and has_been_processed(item['url']):
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
                            p_tok, c_tok = token_tracker.get_and_reset()
                            record_ingestion('web', item['url'], title, user_id=user_id, vault_path=str(vault_file) if vault_file else None, prompt_tokens=p_tok, completion_tokens=c_tok)
                            if vault_file:
                                index_document(str(vault_file), title, analysis)
                            st.expander(f"✅ {title}").markdown(analysis)
                    except Exception as e:
                        p_tok, c_tok = token_tracker.get_and_reset()
                        record_ingestion('web', item['url'], user_id=user_id, status='failed', error_message=str(e), prompt_tokens=p_tok, completion_tokens=c_tok)
                        st.error(f"Error: {e}")
                prog_web.progress((idx+1)/len(selected_web))

# ==========================================
# TAB: DOCGRAB (Deep Discovery)
# ==========================================
with tab_dg:
    st.subheader("🕷️ DocGrab Documentation Engine")
    st.info("Evoluciona de leer artículos a clonar sitios completos de documentación en tu Obsidian.")
    
    dg_url = st.text_input("Root URL de Documentación (o Sitemap)", placeholder="https://docs.ejemplo.com", key="dg_url_input")
    
    col_dg1, col_dg2 = st.columns(2)
    with col_dg1:
        discover_btn = st.button("🔍 Descubrir Estructura", use_container_width=True)
    with col_dg2:
        dg_limit = st.number_input("Máximo de páginas", 5, 500, 20)

    if discover_btn and dg_url:
        from docgrab.discovery.sitemap import discover_urls_from_sitemap
        from docgrab.discovery.spider import extract_sidebar_links
        import requests
        
        with st.spinner("🕵️ Analizando estructura del sitio..."):
            try:
                session = requests.Session()
                session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
                
                all_links = set()
                # 1. Sitemap
                sitemap_url = dg_url if dg_url.endswith(".xml") else f"{dg_url.rstrip('/')}/sitemap.xml"
                s_links = discover_urls_from_sitemap(sitemap_url, session)
                if s_links: all_links.update(s_links)
                
                # 2. Sidebar (Rendered if possible)
                # Para descubrimiento rápido usamos requests, pero si falla el user puede probar rendered
                resp = session.get(dg_url, timeout=10)
                sidebar_links = extract_sidebar_links(resp.text, dg_url, dg_url)
                all_links.update(sidebar_links)
                
                if not all_links:
                    st.warning("No se detectaron sub-enlaces automáticos. ¿Es un sitio SPA? Intentando modo renderizado...")
                    # Aquí podríamos usar playwright, pero por ahora mostramos lo que hay
                
                # Formatear para el editor
                st.session_state.dg_discovered_links = [
                    {"Selected": True, "URL": l, "Path": l.replace(dg_url, "")} 
                    for l in sorted(list(all_links))
                ]
                st.success(f"¡Se detectaron {len(all_links)} páginas potenciales!")
            except Exception as e:
                st.error(f"Error en descubrimiento: {e}")

    if st.session_state.dg_discovered_links:
        st.markdown("### 🛠️ Selección de Documentación")
        edited_dg = st.data_editor(
            pd.DataFrame(st.session_state.dg_discovered_links),
            column_config={
                "Selected": st.column_config.CheckboxColumn("¿Extraer?", default=True),
                "URL": st.column_config.LinkColumn("Enlace Completo"),
                "Path": "Sección/Ruta"
            },
            use_container_width=True, hide_index=True, key="dg_editor"
        )
        st.session_state.dg_discovered_links = edited_dg.to_dict('records')
        selected_dg = [l for l in st.session_state.dg_discovered_links if l.get('Selected')]

        if st.button("🚀 Iniciar Extracción Seleccionada", use_container_width=True):
            if selected_dg:
                import subprocess
                # Para la extracción selectiva, podemos pasar los links uno a uno o usar el limit
                # Pero DocGrab CLI no acepta una lista de links. 
                # Opción A: Modificar DocGrab para aceptar lista.
                # Opción B: Correr DocGrab con limit pero indicando que solo queremos esos.
                # Opción C: Un bucle simple aquí que llame a docgrab por cada link (ineficiente).
                # Mejor Opción: Pasar los links seleccionados a un archivo temporal y que DocGrab lo lea.
                
                prog_dg = st.progress(0)
                user_id = st.session_state.user.id
                vault_path_env = st.session_state.vault_path
                title_slug = dg_url.split("//")[-1].replace("/", "_").replace(".", "_")
                target_dir = os.path.join(vault_path_env, "users", user_id, "40_Docs", title_slug)
                os.makedirs(target_dir, exist_ok=True)

                for idx, item in enumerate(selected_dg):
                    with st.spinner(f"📥 Extrayendo ({idx+1}/{len(selected_dg)}): {item['Path']}"):
                        cmd = [
                            "C:\\Users\\luuis\\AppData\\Local\\Programs\\Python\\Python312\\python.exe", "-m", "docgrab",
                            "--url", item['URL'],
                            "--out", target_dir,
                            "--mode", "rendered",
                            "--limit", "1" # Solo esa página
                        ]
                        subprocess.run(cmd, capture_output=True)
                    prog_dg.progress((idx+1)/len(selected_dg))
                
                st.success(f"✅ ¡Extracción de {len(selected_dg)} páginas completada!")
                st.balloons()
                # Registrar en la base de datos central
                try:
                    from api import record_ingestion
                    record_ingestion('web_deep', dg_url, title_slug, user_id=user_id, vault_path=target_dir, status='success')
                except Exception as e:
                    pass
            else:
                st.warning("Selecciona al menos una página.")

# ==========================================
# TAB 3: CHEF
# ==========================================
with tab3:
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
            prog_chef = st.progress(0)
            for idx, vid in enumerate(selected_chef):
                source_url = vid.get('url', f"https://www.youtube.com/watch?v={vid['id']}")
                if not st.session_state.force_reprocess and has_been_processed(source_url, user_id=user_id):
                    st.info(f"⏭️ Ya procesado: {vid['title']}")
                    prog_chef.progress((idx + 1) / len(selected_chef))
                    continue
                with st.spinner(f"Cocinando: {vid['title']}"):
                    try:
                        t, lang = get_transcript(vid['id'])
                        vid['transcript'] = t
                        recipe = analyze_cooking_video(vid)
                        if "⚠️ ERROR" not in recipe:
                            vault_file = save_note(recipe, f"Receta_{vid['title']}", "50_Recetas")
                            p_tok, c_tok = token_tracker.get_and_reset()
                            record_ingestion('chef', source_url, vid['title'], user_id=user_id, vault_path=str(vault_file) if vault_file else None, prompt_tokens=p_tok, completion_tokens=c_tok)
                            if vault_file:
                                index_document(str(vault_file), vid['title'], recipe)
                            st.expander(f"✅ {vid['title']}").markdown(recipe)
                    except Exception as e:
                        p_tok, c_tok = token_tracker.get_and_reset()
                        record_ingestion('chef', source_url, vid['title'], user_id=user_id, status='failed', error_message=str(e), prompt_tokens=p_tok, completion_tokens=c_tok)
                        st.error(f"Error: {e}")
                prog_chef.progress((idx + 1) / len(selected_chef))

# ==========================================
# TAB 4: RSS
# ==========================================
with tab4:
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
                selected_rss = [a for a in st.session_state.rss_articles if a.get('Selected')]
                for idx, art in enumerate(selected_rss):
                    if not st.session_state.force_reprocess and has_been_processed(art['link']): continue
                    with st.spinner(f"Procesando: {art['title']}"):
                        try:
                            analysis = process_rss_article(art)
                            if "⚠️ ERROR" not in analysis:
                                st.session_state.rss_results[art['link']] = {'title': art['title'], 'content': analysis}
                                vault_file = save_note(analysis, f"RSS_{art['title']}", os.path.join("30_Web", "RSS"))
                                p_tok, c_tok = token_tracker.get_and_reset()
                                record_ingestion('rss', art['link'], art['title'], user_id=user_id, vault_path=str(vault_file) if vault_file else None, prompt_tokens=p_tok, completion_tokens=c_tok)
                                if vault_file:
                                    index_document(str(vault_file), art['title'], analysis)
                                st.expander(f"✅ {art['title']}").markdown(analysis)
                        except Exception as e:
                            p_tok, c_tok = token_tracker.get_and_reset()
                            record_ingestion('rss', art['link'], art['title'], user_id=user_id, status='failed', error_message=str(e), prompt_tokens=p_tok, completion_tokens=c_tok)
                            st.error(f"Error: {e}")

# ==========================================
# TAB 5: AUDIO / PODCAST
# ==========================================
with tab5:
    st.header("🎙️ Ingesta de Audio y Podcasts")
    st.write("Sube archivos de audio para transcribirlos y analizarlos.")
    
    audio_title = st.text_input("Título del Audio / Episodio", placeholder="Ej: Huberman Lab - Sleep")
    audio_tags = st.text_input("Tags (opcional)", placeholder="salud, sueño")
    uploaded_file = st.file_uploader("Selecciona un archivo de audio", type=['mp3', 'wav', 'm4a', 'ogg'])
    
    if uploaded_file is not None and audio_title:
        st.audio(uploaded_file)
        if st.button("🎙️ Analizar Audio"):
            with st.spinner("Procesando archivo..."):
                try:
                    suffix = "." + uploaded_file.name.split('.')[-1] if '.' in uploaded_file.name else ".mp3"
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    mime_map = {".mp3": "audio/mpeg", ".wav": "audio/wav", ".m4a": "audio/mp4", ".ogg": "audio/ogg"}
                    mime_type = mime_map.get(suffix.lower(), "audio/mpeg")
                    result_md = analyze_audio(audio_title, tmp_path, mime_type=mime_type, tags=audio_tags)
                    os.unlink(tmp_path)
                    if "⚠️ ERROR" in result_md:
                        st.error(result_md)
                        p_tok, c_tok = token_tracker.get_and_reset()
                        record_ingestion("audio", f"local_{uuid.uuid4().hex[:8]}", audio_title, user_id=user_id, status="failed", error_message=result_md, prompt_tokens=p_tok, completion_tokens=c_tok)
                    else:
                        filepath = save_note(result_md, audio_title, "60_Audio")
                        st.success(f"✅ Análisis de '{audio_title}' completado.")
                        p_tok, c_tok = token_tracker.get_and_reset()
                        record_ingestion("audio", f"local_{uploaded_file.name}", audio_title, user_id=user_id, vault_path=filepath, status="success", prompt_tokens=p_tok, completion_tokens=c_tok)
                        if filepath:
                            index_document(str(filepath), audio_title, result_md)
                        with st.expander("📄 Ver Análisis Generado", expanded=True):
                            st.markdown(result_md)
                except Exception as e:
                    st.error(f"Error procesando audio: {str(e)}")
                    p_tok, c_tok = token_tracker.get_and_reset()
                    record_ingestion("audio", f"local_{uploaded_file.name}", audio_title, user_id=user_id, status="failed", error_message=str(e), prompt_tokens=p_tok, completion_tokens=c_tok)

# ==========================================
# TAB 6: BUSCADOR SEMANTICO
# ==========================================
with tab6:
    st.header("🔍 Buscador de Conocimiento (RAG)")
    st.write("Hazle preguntas a tu Knowledge Engine en lenguaje natural.")
    
    search_query = st.text_input("¿Qué quieres buscar o saber?", placeholder="Ej. ¿Qué dijo el agente sobre optimización de memoria en GitHub?")
    
    if st.button("🪄 Preguntar al Engine"):
        if search_query:
            with st.spinner("Buscando en la base vectorial y formulando respuesta..."):
                rag_answer = generate_rag_response(search_query)
                st.markdown("### Respuesta del Agente")
                st.markdown(rag_answer)
        else:
            st.warning("Escribe una pregunta para buscar.")

# ==========================================
# TAB 7: ANALYTICS
# ==========================================
with tab7:
    st.header("📊 Knowledge Engine Analytics")
    st.markdown("Estadísticas globales de todas las ingestas registradas en Supabase.")
    stats = get_ingestion_stats(user_id=user_id)
    
    # Custom Metric Cards HTML
    k1, k2, k3, k4 = st.columns(4)
    
    with k1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Ingestas</div>
                <div class="metric-value">{stats.get('total', 0)}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with k2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">✅ Exitosas</div>
                <div class="metric-value" style="color: #10b981;">{stats.get('success', 0)}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with k3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">❌ Fallidas</div>
                <div class="metric-value" style="color: #ff4b4b;">{stats.get('failed', 0)}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with k4:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">💸 Costo Estimado</div>
                <div class="metric-value">${stats.get('estimated_cost_usd', 0):.4f}</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown(f"""
            <div class="metric-card" style="text-align: left;">
                <div class="metric-label">Total Prompt Tokens (Input)</div>
                <div class="metric-value" style="font-size: 1.5rem;">{stats.get('total_prompt_tokens', 0):,}</div>
            </div>
        """, unsafe_allow_html=True)
    with col_t2:
        st.markdown(f"""
            <div class="metric-card" style="text-align: left;">
                <div class="metric-label">Total Completion Tokens (Output)</div>
                <div class="metric-value" style="font-size: 1.5rem;">{stats.get('total_completion_tokens', 0):,}</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    if stats.get("by_type"):
        st.subheader("📂 Ingestas por Tipo de Fuente")
        type_df = pd.DataFrame(stats["by_type"], columns=["Fuente", "Cantidad"])
        st.bar_chart(type_df.set_index("Fuente"))

    if stats.get("by_date"):
        st.subheader("📅 Timeline de Procesamiento (últimos 30 días)")
        date_df = pd.DataFrame(stats["by_date"], columns=["Fecha", "Cantidad"])
        date_df = date_df.sort_values("Fecha")
        st.line_chart(date_df.set_index("Fecha"))

    st.divider()

    if stats.get("recent"):
        st.subheader("🕐 Últimas 10 Ingestas")
        recent_df = pd.DataFrame(stats["recent"])
        display_cols = ["source_type", "title", "source_url", "status", "processed_at"]
        available_cols = [c for c in display_cols if c in recent_df.columns]
        st.dataframe(
            recent_df[available_cols].rename(columns={
                "source_type": "Tipo", "title": "Título", "source_url": "URL", "status": "Estado", "processed_at": "Procesado",
            }),
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("Aún no hay ingestas registradas.")

    all_ingestions = list_recent_ingestions(limit=500, user_id=user_id)
    if all_ingestions:
        csv_data = pd.DataFrame(all_ingestions).to_csv(index=False)
        st.download_button("📥 Exportar historial (CSV)", csv_data, "ingestion_history.csv", "text/csv")

# ==========================================
# TAB 8: OBSIDIAN SYNC
# ==========================================
with tab8:
    st.subheader("🧠 Obsidian Knowledge Sync")
    c_s1, c_s2 = st.columns(2)
    
    with c_s1:
        if st.button("🔄 Sincronizar Ahora"):
            with st.spinner("Sincronizando agentes..."):
                msg = sync_all_to_obsidian(st.session_state.vault_path)
                st.success(msg)
                
    with c_s2:
        # Botón para descargar todas las notas en ZIP
        user_vault_path = os.path.join(st.session_state.vault_path, "users", user_id)
        if os.path.exists(user_vault_path):
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(user_vault_path):
                    for file in files:
                        abs_path = os.path.join(root, file)
                        rel_path = os.path.relpath(abs_path, user_vault_path)
                        zf.write(abs_path, rel_path)
            
            st.download_button(
                label="📥 Descargar todo mi Knowledge (ZIP)",
                data=buf.getvalue(),
                file_name=f"knowledge_base_{st.session_state.user.email.split('@')[0]}.zip",
                mime="application/zip",
                use_container_width=True
            )
        else:
            st.info("Aún no tienes notas generadas para descargar.")

# ==========================================
# TAB 9: NOTEBOOKLM PACK
# ==========================================
with tab9:
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
    if all_sources:
        st.table(pd.DataFrame(all_sources))
        if st.button("📝 Generar Contexto Maestro"):
            ctx_md = generate_context_markdown(st.session_state.yt_audit_results, st.session_state.gh_audit_results, st.session_state.web_audit_results, st.session_state.rss_results)
            save_note(ctx_md, f"NotebookLM_Context_{datetime.now().strftime('%Y%m%d')}", "40_NotebookLM")
            st.success("Contexto Maestro guardado exitosamente en el Vault.")

