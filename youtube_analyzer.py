import time
from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi
from config import generate_with_retry


def get_video_list(url, limit=None):
    """Obtiene la lista de videos con metadatos extendidos."""
    if "/@" in url and "/videos" not in url and "/search" not in url:
        url = url.rstrip("/") + "/videos"

    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'playlist_items': f'1-{limit}' if limit else None,
    }

    videos = []
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            entries = info.get('entries', [info])
            for entry in entries:
                if not entry:
                    continue
                v_id = entry.get('id')
                if v_id and len(v_id) == 11:
                    raw_date = entry.get('upload_date', 'N/A')
                    fmt_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}" if len(raw_date) == 8 else raw_date
                    videos.append({
                        'id': v_id,
                        'title': entry.get('title'),
                        'url': f"https://www.youtube.com/watch?v={v_id}",
                        'views': entry.get('view_count', 0),
                        'date': fmt_date,
                        'description': entry.get('description', 'Sin descripción')
                    })
        except Exception as e:
            raise Exception(f"Error yt-dlp: {e}")

    return videos


def get_transcript(video_id):
    """Descarga la transcripción y retorna (texto, idioma)."""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            transcript = transcript_list.find_transcript(['es', 'en'])
        except Exception:
            transcript = next(iter(transcript_list))

        data = transcript.fetch()
        return " ".join([t['text'] for t in data]), transcript.language_code
    except Exception:
        return None, None


def analyze_video_content(video_data, transcript, transcript_lang=None):
    """Genera una nota de Obsidian a partir de los datos del video usando Gemini."""
    content = f"Título: {video_data['title']}\n"
    if transcript:
        content += f"\nTranscripción (fragmento): {transcript[:10000]}"
    else:
        content += f"\nDescripción: {video_data['description'][:2000]}"

    instruction = "Genera el reporte en ESPAÑOL." if transcript_lang == 'es' else "Generate the report in ENGLISH."

    prompt = (
        "Actúa como un experto en gestión del conocimiento técnico. Genera una nota para Obsidian.\n\n"
        "REQUISITO CRÍTICO: Comienza SIEMPRE con un bloque YAML Properties exactamente así:\n"
        "---\n"
        "tipo: video_research\n"
        f"fuente: \"{video_data.get('url', 'N/A')}\"\n"
        f"canal: \"{video_data.get('channel', 'N/A')}\"\n"
        f"fecha_video: {video_data.get('date', 'N/A')}\n"
        "estado: procesado\n"
        f"idioma_original: {transcript_lang}\n"
        "---\n\n"
        f"# {video_data.get('title', 'Análisis de Video')}\n\n"
        f"{instruction}\n"
        "SECCIONES REQUERIDAS:\n"
        "1. **Resumen Ejecutivo**: 3 puntos clave.\n"
        "2. **Stack Tecnológico**: Si se mencionan lenguajes/herramientas.\n"
        "3. **Decisiones de Arquitectura / Lógica**: Por qué y cómo funciona lo explicado.\n"
        "4. **Action Items / Hallazgos**: Ideas accionables sacadas del video.\n\n"
        f"CONTENIDO:\n{content}"
    )

    return generate_with_retry(prompt)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    try:
        vids = get_video_list(args.url, limit=args.limit)
        for v in vids:
            t, lang = get_transcript(v['id'])
            a = analyze_video_content(v, t, lang)
            print(f"--- {v['title']} ---\n{a}\n")
            time.sleep(5)
    except Exception as e:
        print(e)
