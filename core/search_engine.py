import textwrap
from core.db import supabase
from config import generate_embedding, generate_with_retry
from core.prompt_loader import render_prompt

def chunk_text(text: str, max_chunk_size: int = 1500) -> list[str]:
    """Divide un texto largo en fragmentos más pequeños para vectorizar."""
    # Envolvemos el texto respetando espacios y nuevas líneas lo mejor posible
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) <= max_chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # Si un párrafo es excesivamente largo, lo forzamos a cortarse
            if len(para) > max_chunk_size:
                wrapped = textwrap.wrap(para, width=max_chunk_size)
                chunks.extend(wrapped)
                current_chunk = ""
            else:
                current_chunk = para + "\n\n"
                
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

def index_document(source_path: str, title: str, content: str, user_id: str = None):
    """Genera embeddings para el documento y lo guarda en Supabase."""
    chunks = chunk_text(content)
    records_to_insert = []

    for chunk in chunks:
        if not chunk.strip():
            continue

        vector = generate_embedding(chunk)
        if not vector:
            continue

        records_to_insert.append({
            "user_id": user_id,
            "source_path": source_path,
            "source_title": title,
            "content": chunk,
            "embedding": vector
        })

    if records_to_insert:
        try:
            supabase.table("document_chunks").insert(records_to_insert).execute()
        except Exception as e:
            print(f"Error indexando en Supabase: {e}")

def search_knowledge_base(query: str, match_threshold: float = 0.5, match_count: int = 5, user_id: str = None) -> list[dict]:
    """Busca en el Vault (vía Supabase) los fragmentos más relevantes."""
    query_vector = generate_embedding(query)
    if not query_vector:
        return []

    try:
        response = supabase.rpc(
            "match_document_chunks",
            {
                "query_embedding": query_vector,
                "match_threshold": match_threshold,
                "match_count": match_count,
                "filter_user_id": user_id
            }
        ).execute()

        return response.data
    except Exception as e:
        print(f"Error buscando en Supabase: {e}")
        return []

def generate_rag_response(query: str, user_id: str = None) -> str:
    """Busca contexto y pide a Gemini que responda basándose en los resultados."""
    results = search_knowledge_base(query, user_id=user_id)
    
    if not results:
        return "No encontré información relevante en el Vault sobre tu pregunta."
        
    # Armar el contexto
    context = "\n\n---\n\n".join([
        f"Fuente: {r['source_title']} ({r['source_path']})\nContenido: {r['content']}" 
        for r in results
    ])
    
    # Podríamos usar un template de Jinja2 aquí en el futuro, pero lo haremos directo por ahora
    prompt = f"""Eres un asistente experto para Luis en su Knowledge Engine (Deep Audit).
Usa la siguiente información extraída de su sistema de gestión del conocimiento (Vault) para responder a su pregunta.
Siempre debes citar la fuente de donde sacaste la información.
Si la información no está en el contexto, díselo claramente. No inventes respuestas.

### Contexto Recuperado de la Base de Conocimiento
{context}

### Pregunta del Usuario
{query}

### Tu Respuesta Detallada y Citada
"""
    
    response = generate_with_retry(prompt)
    
    # Anexar las fuentes crudas al final de la respuesta para transparencia
    sources_md = "\n\n### 🔗 Fuentes Consultadas\n"
    unique_sources = set()
    for r in results:
        if r['source_path'] not in unique_sources:
            sources_md += f"- **{r['source_title']}** (`{r['source_path']}`)\n"
            unique_sources.add(r['source_path'])
            
    return response + sources_md
