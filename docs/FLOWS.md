# Data Flows: Deep Audit Knowledge Engine

## 1. Flujo de Auditoría YouTube

```mermaid
sequenceDiagram
    participant U as Usuario
    participant S as Streamlit App
    participant C as config.py
    participant A as youtube_analyzer
    participant G as Gemini API
    participant V as Obsidian Vault

    U->>S: Ingresa URL Canal
    S->>A: get_video_list(url)
    A-->>S: Lista de Metadatos
    U->>S: Selecciona Videos
    S->>S: transcript_cache[id]?
    alt No está en caché
        S->>A: get_transcript(vid_id)
        A-->>S: (texto, idioma)
        S->>S: Guarda en transcript_cache
    end
    S->>C: generate_with_retry(prompt)
    C->>G: Prompt con transcripción
    G-->>C: Markdown Report
    C-->>S: Texto generado
    S->>V: save_note("10_YouTube/")
    S-->>U: Expander + ZIP descargable
```

---

## 2. Flujo de Auditoría GitHub

```mermaid
sequenceDiagram
    participant S as Streamlit App
    participant GH as GitHub API
    participant GA as github_analyzer
    participant C as config.py
    participant G as Gemini API

    S->>GH: get_user_repos(user)
    GH-->>S: Lista de Repos
    S->>GH: get_repo_structure(Trees API)
    GH-->>S: Full Tree JSON
    S->>GA: identify_critical_files(tree)
    GA-->>S: Hasta 12 File Paths (ADN)
    loop Por cada archivo crítico
        S->>GH: fetch_file_content(path)
        GH-->>S: Contenido decodificado (Base64)
    end
    S->>C: generate_with_retry(prompt)
    C->>G: Prompt con Tree + ADN
    G-->>C: Technical Wiki MD
    C-->>S: Texto generado
    S->>S: save_note("20_GitHub/")
```

---

## 3. Flujo de Ingesta Web

```mermaid
sequenceDiagram
    participant S as Streamlit App
    participant W as web_analyzer
    participant C as config.py
    participant G as Gemini API

    S->>W: fetch_web_content(url)
    W->>W: requests.get + BeautifulSoup limpieza
    W-->>S: title + text[:15000]
    S->>C: generate_with_retry(prompt)
    C->>G: Prompt Zettelkasten
    G-->>C: Nota MD estructurada
    C-->>S: Texto generado
    S->>S: save_note("30_Web/")
```

---

## 4. Flujo RSS Monitor (Sprint 4 — Planeado)

```mermaid
sequenceDiagram
    participant U as Usuario
    participant S as Streamlit App
    participant RM as rss_manager
    participant DB as rss_db (SQLite)
    participant W as web_analyzer
    participant C as config.py
    participant V as Obsidian Vault

    U->>S: Agrega feed (nombre + URL)
    S->>DB: add_feed(name, url)

    U->>S: "Revisar feeds ahora"
    S->>DB: get_active_feeds()
    DB-->>S: Lista de feeds

    loop Por cada feed
        S->>RM: check_feed(feed)
        RM->>RM: feedparser.parse(url)
        loop Por cada entry nueva
            RM->>DB: is_seen(feed_id, url)?
            alt No visto
                RM->>W: fetch_web_content(entry.url)
                W-->>RM: Contenido limpio
                RM->>C: generate_with_retry(prompt)
                C-->>RM: Nota MD
                RM->>V: save_note("30_Web/RSS/")
                RM->>DB: mark_seen(feed_id, url, title, filename)
            end
        end
    end
    S-->>U: Tabla de historial actualizada
```

---

## 5. Flujo NotebookLM Source Pack (Sprint 5 — Planeado)

```mermaid
sequenceDiagram
    participant U as Usuario
    participant S as Streamlit App
    participant NP as notebooklm_pack
    participant DB as rss_db (SQLite)
    participant C as config.py
    participant G as Gemini API

    U->>S: Abre tab NotebookLM Pack
    S->>NP: collect_sources(session_state, rss_db)
    NP->>S: yt_audit_results → URLs YouTube
    NP->>S: web_audit_results → URLs Web
    NP->>DB: get_all_processed_urls()
    DB-->>NP: URLs históricas de RSS
    NP-->>S: Lista deduplicada {url, tipo, titulo}

    U->>S: Selecciona subset de fuentes
    U->>S: "Generar Pack"

    S->>NP: build_url_txt(selected)
    NP-->>S: String con URLs (una por línea)
    S-->>U: Download "notebooklm_sources.txt"

    S->>NP: build_context_note(selected, analyses)
    NP->>C: generate_with_retry(prompt consolidado)
    C->>G: Resúmenes de todas las fuentes
    G-->>C: Nota MD de contexto enriquecida
    C-->>NP: Texto generado
    NP-->>S: Nota MD lista
    S-->>U: Download "notebooklm_context.md"
```

---

## 6. Flujo Audio/Podcast (Sprint 6 — Planeado)

```mermaid
sequenceDiagram
    participant U as Usuario
    participant S as Streamlit App
    participant PA as podcast_analyzer
    participant AT as audio_transcriber
    participant WH as faster-whisper
    participant YA as youtube_analyzer
    participant C as config.py
    participant V as Obsidian Vault

    alt Modo: Archivo subido
        U->>S: Sube .mp3/.wav/.m4a
        S->>AT: transcribe_bytes(audio_bytes)
        AT->>AT: Escribe temp file
        AT->>WH: model.transcribe(path)
        WH-->>AT: segments + idioma
        AT->>AT: Borra temp file
        AT-->>S: (texto_completo, idioma)
        S->>PA: build_metadata_from_upload(filename)
    else Modo: URL de podcast
        U->>S: Ingresa URL feed o episodio
        S->>PA: detect_and_extract(url)
        PA->>PA: feedparser / requests / yt-dlp
        PA-->>S: audio_path local
        S->>AT: transcribe_file(path)
        AT->>WH: model.transcribe(path)
        WH-->>AT: segments + idioma
        AT-->>S: (texto_completo, idioma)
        S->>PA: build_metadata_from_feed(entry, feed)
    end

    S->>YA: analyze_video_content(metadata, texto, idioma)
    YA->>C: generate_with_retry(prompt)
    C-->>YA: Nota MD
    YA-->>S: Markdown generado
    S->>V: save_note("60_Podcasts/")
    S-->>U: Expander con nota + ZIP
```
