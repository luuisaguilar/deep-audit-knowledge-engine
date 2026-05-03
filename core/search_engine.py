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

def search_knowledge_base(query: str, match_threshold: float = 0.2, match_count: int = 10, user_id: str = None) -> list[dict]:
    """
    Busca en el Vault usando Búsqueda Híbrida (Vector + Full-Text Search) con RRF.
    """
    query_vector = generate_embedding(query)
    if not query_vector:
        return []

    try:
        response = supabase.rpc(
            "hybrid_search_chunks",
            {
                "query_text": query,
                "query_embedding": query_vector,
                "match_threshold": match_threshold,
                "match_count": match_count,
                "filter_user_id": user_id
            }
        ).execute()

        results = response.data
        if results:
            print(f"Búsqueda Híbrida: {len(results)} resultados. Top score: {results[0]['score']:.4f}")
        return results
    except Exception as e:
        print(f"Error en búsqueda híbrida: {e}")
        return []

def dedup_results(results: list[dict], threshold: float = 0.85) -> list[dict]:
    """
    Deduplicación de resultados basada en similitud Jaccard de conjuntos de palabras.
    Inspirado en GBrain dedup.ts
    """
    kept = []
    for r in results:
        r_text = r.get('content', '').lower()
        r_words = set(re.findall(r'\w+', r_text))
        
        is_duplicate = False
        for k in kept:
            k_text = k.get('content', '').lower()
            k_words = set(re.findall(r'\w+', k_text))
            
            if not r_words or not k_words:
                continue
                
            intersection = r_words.intersection(k_words)
            union = r_words.union(k_words)
            jaccard = len(intersection) / len(union)
            
            if jaccard > threshold:
                is_duplicate = True
                break
        
        if not is_duplicate:
            kept.append(r)
            
    return kept

def generate_rag_response(query: str, user_id: str = None) -> str:
    """
    RAG de Dos Pasos con Deduplicación Semántica:
    1. Búsqueda Híbrida para encontrar anclas.
    2. Expansión estructural vía Grafo de Conocimiento.
    3. Deduplicación para limpiar el contexto.
    """
    # Paso 1: Búsqueda Híbrida (Anclas)
    anchor_results = search_knowledge_base(query, user_id=user_id, match_count=8)
    
    if not anchor_results:
        return "No encontré información relevante en el Vault sobre tu pregunta."
        
    # Paso 2: Expansión Estructural
    source_paths = list(set([r['source_path'] for r in anchor_results if r.get('source_path')]))
    
    expanded_results = []
    try:
        expansion_response = supabase.rpc(
            "expand_search_context",
            {
                "base_source_paths": source_paths,
                "max_hops": 1,
                "limit_per_hop": 3
            }
        ).execute()
        expanded_results = expansion_response.data or []
    except Exception as e:
        print(f"Error expandiendo contexto: {e}")

    # Combinar y Deduplicar
    all_results = anchor_results + expanded_results
    unique_results = dedup_results(all_results)
    
    if len(all_results) != len(unique_results):
        print(f"Deduplicación: {len(all_results)} -> {len(unique_results)} fragmentos únicos.")

    # Armar el contexto para el LLM
    context_blocks = []
    for r in unique_results:
        tag = "[ANCLA]" if r in anchor_results else "[RELACIONADO]"
        context_blocks.append(f"{tag} Fuente: {r['source_title']} ({r['source_path']})\nContenido: {r['content']}")
    
    context = "\n\n---\n\n".join(context_blocks)
    
    prompt = f"""Eres un asistente experto para Luis en su Knowledge Engine (Deep Audit).
Usa la siguiente información del Vault para responder. El contexto incluye resultados directos [ANCLA]
y conocimiento conectado a través del grafo [RELACIONADO].

Siempre debes citar la fuente de donde sacaste la información.
Si la información no está en el contexto, díselo claramente. No inventes respuestas.

### Contexto Recuperado
{context}

### Pregunta del Usuario
{query}

### Tu Respuesta Detallada y Citada
"""
    
    response = generate_with_retry(prompt)
    
    sources_md = "\n\n### 🔗 Fuentes Consultadas\n"
    unique_sources = {}
    for r in all_results:
        path = r['source_path']
        if path not in unique_sources:
            unique_sources[path] = r['source_title']
            
    for path, title in unique_sources.items():
        sources_md += f"- **{title}** (`{path}`)\n"
            
    return response + sources_md
