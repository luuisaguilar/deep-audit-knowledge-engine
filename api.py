from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import httpx
import re
import tempfile
from typing import Optional, List
from youtube_analyzer import get_video_list, get_transcript, analyze_video_content
from github_analyzer import get_user_repos, get_repo_structure, identify_critical_files, fetch_file_content, analyze_repository_wiki
from web_analyzer import fetch_web_content, analyze_web_content
from cooking_analyzer import analyze_cooking_video
from audio_analyzer import analyze_audio
from rss_db import get_feeds, add_feed, remove_feed
from rss_manager import fetch_new_articles, process_rss_article
from notebooklm_pack import generate_source_list, generate_context_markdown
from knowledge_sync import sync_all_to_obsidian
from core.db import record_ingestion, has_been_processed
from core.search_engine import index_document, generate_rag_response, search_knowledge_base
from config import token_tracker
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Deep Audit Knowledge Engine API", version="1.0.0")

class InspectRequest(BaseModel):
    url: str
    user_id: Optional[str] = "admin" # Valor por defecto para retrocompatibilidad simple

class InspectResponse(BaseModel):
    url: str
    source_type: str
    title_preview: Optional[str] = None
    available_actions: List[str]

class ProcessRequest(BaseModel):
    url: str
    action: str
    user_id: Optional[str] = "admin"
    force_reprocess: bool = False
    depth: Optional[str] = "20"  # Nuevo campo para DocGrab
    callback_url: Optional[str] = None

def identify_url_type(url: str) -> str:
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    elif "github.com" in url:
        return "github"
    elif url.endswith(".mp3") or url.endswith(".wav"):
        return "audio"
    else:
        return "web"

@app.post("/api/v1/inspect-url", response_model=InspectResponse)
async def inspect_url(req: InspectRequest):
    """
    Recibe una URL cruda (ej. desde Telegram/n8n) y devuelve qué tipo de contenido es
    y qué opciones de procesamiento tiene el usuario.
    """
    url_type = identify_url_type(req.url)
    title_preview = "Contenido"
    actions = []

    try:
        if url_type == "youtube":
            vids = get_video_list(req.url, limit=1)
            if vids:
                title_preview = vids[0]["title"]
            actions = ["Deep Audit (Dev)", "Extraer Receta (Chef)"]
        elif url_type == "github":
            # Extraer repo name de github.com/user/repo
            match = re.search(r'github\.com/([^/]+)/([^/]+)', req.url)
            if match:
                title_preview = f"{match.group(1)}/{match.group(2)}"
            actions = ["Generar Wiki Técnica"]
        elif url_type == "web":
            actions = ["Resumir Artículo", "Extraer Sitio Completo (DocGrab)"]
    except Exception as e:
        title_preview = f"Error obteniendo preview: {e}"

    return InspectResponse(
        url=req.url,
        source_type=url_type,
        title_preview=title_preview,
        available_actions=actions
    )

async def send_callback(callback_url: str, payload: dict):
    if not callback_url:
        return
    try:
        async with httpx.AsyncClient() as client:
            await client.post(callback_url, json=payload)
    except Exception as e:
        print(f"Error sending callback to {callback_url}: {e}")

def background_process(req: ProcessRequest):
    """Procesamiento pesado ejecutado en segundo plano."""
    source_type = identify_url_type(req.url)
    vault_path_env = os.getenv("VAULT_PATH", "/mnt/obsidian-vault")
    
    # Check deduplication
    if not req.force_reprocess and has_been_processed(req.url, user_id=req.user_id):
        print(f"Skipping already processed URL: {req.url} for user {req.user_id}")
        import asyncio
        asyncio.run(send_callback(req.callback_url, {"status": "skipped", "message": "Ya procesado", "url": req.url}))
        return

    result_md = ""
    title = "Unknown"
    error = None
    saved_path = None
    
    # Helpers for saving with User Isolation
    def save_note_api(content, filename, subfolder, u_id):
        if not filename.endswith(".md"): filename += ".md"
        basename, ext = os.path.splitext(filename)
        clean_base = "".join([c if c.isalnum() or c in (' ', '_', '-') else "_" for c in basename])
        clean_name = f"{clean_base}{ext}"
        
        target_dir = os.path.join(vault_path_env, "users", u_id, subfolder)
        os.makedirs(target_dir, exist_ok=True)
        filepath = os.path.join(target_dir, clean_name)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

    try:
        if source_type == "youtube":
            vids = get_video_list(req.url, limit=1)
            if not vids: raise Exception("No se encontró video.")
            vid = vids[0]
            title = vid["title"]
            t, lang = get_transcript(vid["id"])
            if req.action == "Extraer Receta (Chef)":
                vid["transcript"] = t
                result_md = analyze_cooking_video(vid)
                subfolder = "50_Recetas"
                prefix = "Receta_"
                db_type = "chef"
            else:
                result_md = analyze_video_content(vid, t, lang)
                subfolder = "10_YouTube"
                prefix = "YT_"
                db_type = "youtube"
                
            if "⚠️ ERROR" not in result_md:
                saved_path = save_note_api(result_md, f"{prefix}{title}", subfolder, req.user_id)
                index_document(saved_path, title, result_md)

        elif source_type == "github":
            match = re.search(r'github\.com/([^/]+)/([^/]+)', req.url)
            if not match: raise Exception("URL de GitHub inválida.")
            owner, repo_name = match.group(1), match.group(2)
            title = repo_name
            db_type = "github"
            
            structure = get_repo_structure(owner, repo_name, "main")
            crit_files = identify_critical_files(structure)
            files_data = {f: fetch_file_content(owner, repo_name, f) for f in crit_files if fetch_file_content(owner, repo_name, f)}
            repo_mock = {"name": repo_name, "owner": {"login": owner}, "description": "", "html_url": req.url}
            result_md = analyze_repository_wiki(owner, repo_name, repo_mock, structure, files_data)
            
            if "⚠️ ERROR" not in result_md:
                saved_path = save_note_api(result_md, f"WIKI_{title}", "20_GitHub", req.user_id)
                index_document(saved_path, title, result_md)

        elif source_type == "web":
            db_type = "web"
            if req.action == "Extraer Sitio Completo (DocGrab)":
                import subprocess
                target_dir = os.path.join(vault_path_env, "users", req.user_id, "40_Docs", title.replace(" ", "_"))
                os.makedirs(target_dir, exist_ok=True)
                
                # Usar el parámetro depth (limit en docgrab)
                limit = req.depth if req.depth else "20"
                
                cmd = [
                    "python", "-m", "docgrab",
                    "--url", req.url,
                    "--out", target_dir,
                    "--mode", "rendered",
                    "--limit", limit
                ]
                
                process = subprocess.run(cmd, capture_output=True, text=True)
                if process.returncode != 0:
                    error = f"DocGrab Error: {process.stderr}"
                    result_md = "⚠️ ERROR"
                else:
                    saved_path = target_dir
                    result_md = f"DocGrab finalizó exitosamente (límite {limit})."
            else:
                web_data = fetch_web_content(req.url)
                title = web_data.get("title", "Web_Note")
                result_md = analyze_web_content(web_data)
                if "⚠️ ERROR" not in result_md:
                    saved_path = save_note_api(result_md, f"WEB_{title}", "30_Web", req.user_id)
                    index_document(saved_path, title, result_md)

        # Grabar en BD
        p_tok, c_tok = token_tracker.get_and_reset()
        if error or "⚠️ ERROR" in result_md:
            record_ingestion(db_type, req.url, title, user_id=req.user_id, status="failed", error_message=error or result_md, prompt_tokens=p_tok, completion_tokens=c_tok)
        else:
            record_ingestion(db_type, req.url, title, user_id=req.user_id, vault_path=saved_path, status="success", prompt_tokens=p_tok, completion_tokens=c_tok)

        # Llamar a n8n de vuelta
        import asyncio
        asyncio.run(send_callback(req.callback_url, {
            "status": "success" if not error else "failed",
            "title": title,
            "url": req.url,
            "vault_path": saved_path,
            "error": error
        }))

    except Exception as e:
        p_tok, c_tok = token_tracker.get_and_reset()
        record_ingestion(source_type, req.url, title, user_id=req.user_id, status="failed", error_message=str(e), prompt_tokens=p_tok, completion_tokens=c_tok)
        import asyncio
        asyncio.run(send_callback(req.callback_url, {
            "status": "failed",
            "url": req.url,
            "error": str(e)
        }))

class AnalyzeRequest(BaseModel):
    url: str
    user_id: Optional[str] = "web-user"
    depth: Optional[str] = "20"

@app.post("/analyze/youtube")
async def analyze_youtube(req: AnalyzeRequest, background_tasks: BackgroundTasks):
    process_req = ProcessRequest(url=req.url, action="Deep Audit (Dev)", user_id=req.user_id)
    background_tasks.add_task(background_process, process_req)
    return {"message": "Análisis de YouTube encolado.", "url": req.url}

@app.post("/analyze/docgrab")
async def analyze_docgrab(req: AnalyzeRequest, background_tasks: BackgroundTasks):
    process_req = ProcessRequest(url=req.url, action="Extraer Sitio Completo (DocGrab)", user_id=req.user_id, depth=req.depth)
    background_tasks.add_task(background_process, process_req)
    return {"message": "DocGrab encolado.", "url": req.url, "depth": req.depth}

@app.post("/analyze/github")
async def analyze_github(req: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Genera wiki técnica de un repositorio de GitHub."""
    process_req = ProcessRequest(url=req.url, action="Generar Wiki Técnica", user_id=req.user_id)
    background_tasks.add_task(background_process, process_req)
    return {"message": "Análisis de GitHub encolado.", "url": req.url}

@app.post("/analyze/web")
async def analyze_web(req: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Extrae y analiza el contenido de un artículo web."""
    process_req = ProcessRequest(url=req.url, action="Resumir Artículo", user_id=req.user_id)
    background_tasks.add_task(background_process, process_req)
    return {"message": "Artículo web encolado.", "url": req.url}

@app.post("/analyze/chef")
async def analyze_chef(req: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Extrae recetas de videos de cocina en YouTube."""
    process_req = ProcessRequest(url=req.url, action="Extraer Receta (Chef)", user_id=req.user_id)
    background_tasks.add_task(background_process, process_req)
    return {"message": "Extracción de receta encolada.", "url": req.url}

@app.post("/analyze/audio")
async def analyze_audio_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Form(default="web-user")
):
    """Sube un archivo de audio para transcripción y análisis."""
    vault_path_env = os.getenv("VAULT_PATH", "/mnt/obsidian-vault")

    contents = await file.read()
    suffix = os.path.splitext(file.filename or "audio.mp3")[1] or ".mp3"

    def _process_audio():
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        try:
            result_md = analyze_audio(tmp_path)
            audio_title = os.path.splitext(file.filename or "audio")[0]
            target_dir = os.path.join(vault_path_env, "users", user_id, "60_Audio")
            os.makedirs(target_dir, exist_ok=True)
            clean_name = "".join([c if c.isalnum() or c in (' ', '_', '-') else "_" for c in audio_title])
            filepath = os.path.join(target_dir, f"{clean_name}.md")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(result_md)
            index_document(filepath, audio_title, result_md, user_id=user_id)
            p_tok, c_tok = token_tracker.get_and_reset()
            record_ingestion("audio", tmp_path, audio_title, user_id=user_id, vault_path=filepath, status="success", prompt_tokens=p_tok, completion_tokens=c_tok)
        except Exception as e:
            p_tok, c_tok = token_tracker.get_and_reset()
            record_ingestion("audio", file.filename or "audio", file.filename or "audio", user_id=user_id, status="failed", error_message=str(e), prompt_tokens=p_tok, completion_tokens=c_tok)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    background_tasks.add_task(_process_audio)
    return {"message": f"Audio '{file.filename}' encolado para análisis."}

class RagRequest(BaseModel):
    query: str
    user_id: Optional[str] = "web-user"

@app.get("/search/knowledge-base")
async def search_kb_endpoint(query: str, limit: int = 5, user_id: str = "web-user"):
    """Búsqueda rápida (Híbrida + RRF) para el dropdown del topbar."""
    results = search_knowledge_base(query, match_count=limit, user_id=user_id)
    return results

@app.post("/search/rag")
async def search_rag(req: RagRequest):
    """Búsqueda semántica RAG sobre el Vault del usuario."""
    answer = generate_rag_response(req.query, user_id=req.user_id)
    sources = []
    # Extraer fuentes del formato de generate_rag_response si incluye la sección de fuentes
    if "### 🔗 Fuentes Consultadas" in answer:
        parts = answer.split("### 🔗 Fuentes Consultadas")
        answer = parts[0].strip()
        for line in parts[1].strip().split("\n"):
            if "`" in line:
                src = line.split("`")[1]
                sources.append(src)
    return {"answer": answer, "sources": sources}

class RssFeedRequest(BaseModel):
    url: str
    user_id: Optional[str] = "web-user"

@app.post("/rss/add-feed")
async def rss_add_feed(req: RssFeedRequest):
    """Agrega un feed RSS a la base de datos."""
    try:
        add_feed(req.url)
        return {"message": "Feed agregado correctamente.", "url": req.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/rss/fetch-all")
async def rss_fetch_all(background_tasks: BackgroundTasks):
    """Procesa todos los feeds RSS registrados."""
    background_tasks.add_task(fetch_new_articles)
    return {"message": "Procesamiento de feeds RSS encolado."}

class NotebookLMRequest(BaseModel):
    topic: str
    user_id: Optional[str] = "web-user"

@app.post("/analyze/notebooklm")
async def analyze_notebooklm(req: NotebookLMRequest):
    """Genera un pack de fuentes para NotebookLM sobre un tema."""
    try:
        source_list = generate_source_list(req.topic)
        context_md = generate_context_markdown(req.topic)
        vault_path_env = os.getenv("VAULT_PATH", "/mnt/obsidian-vault")
        target_dir = os.path.join(vault_path_env, "users", req.user_id, "70_NotebookLM")
        os.makedirs(target_dir, exist_ok=True)
        clean_topic = "".join([c if c.isalnum() or c in (' ', '_', '-') else "_" for c in req.topic])
        with open(os.path.join(target_dir, f"sources_{clean_topic}.md"), "w", encoding="utf-8") as f:
            f.write(source_list)
        with open(os.path.join(target_dir, f"context_{clean_topic}.md"), "w", encoding="utf-8") as f:
            f.write(context_md)
        return {"message": "Pack generado.", "topic": req.topic}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SyncRequest(BaseModel):
    user_id: Optional[str] = None

@app.post("/sync/obsidian")
async def sync_obsidian(req: SyncRequest = SyncRequest()):
    """Sincroniza todas las notas con Obsidian."""
    try:
        stats = sync_all_to_obsidian()
        return {"message": "Sincronización completada.", "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class DeduplicateRequest(BaseModel):
    user_id: Optional[str] = "web-user"

@app.post("/vault/deduplicate")
async def vault_deduplicate(req: DeduplicateRequest):
    user_id = req.user_id or "web-user"
    """
    Escanea el Vault del usuario y elimina fragmentos semánticamente redundantes (>0.90 Jaccard).
    Útil para "limpiar" el sistema de información repetida.
    """
    try:
        from core.search_engine import dedup_results
        # Obtener todos los chunks del usuario
        response = supabase.table("document_chunks").select("*").eq("user_id", user_id).execute()
        all_chunks = response.data
        if not all_chunks:
            return {"message": "No hay fragmentos para procesar."}
            
        unique_chunks = dedup_results(all_chunks, threshold=0.90)
        
        to_delete = [c['id'] for c in all_chunks if c not in unique_chunks]
        
        if to_delete:
            # Supabase delete por lista de IDs
            supabase.table("document_chunks").delete().in_("id", to_delete).execute()
            
        return {
            "total_before": len(all_chunks),
            "total_after": len(unique_chunks),
            "deleted": len(to_delete),
            "message": f"Se eliminaron {len(to_delete)} fragmentos redundantes."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/api/v1/process-url")
async def process_url(req: ProcessRequest, background_tasks: BackgroundTasks):
    """
    Recibe la URL y la acción seleccionada. Envía la tarea a segundo plano (background)
    y retorna Inmediatamente 202 Accepted.
    """
    background_tasks.add_task(background_process, req)
    return {"message": "Procesamiento encolado. Te notificaremos al terminar.", "url": req.url, "action": req.action}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
