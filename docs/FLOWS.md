# Data Flows: Deep Audit Knowledge Engine

## 1. Flujo de Auditoría YouTube

```mermaid
sequenceDiagram
    participant U as Usuario
    participant S as Streamlit App
    participant DB as knowledge.db
    participant PT as prompts/youtube_analysis.md
    participant A as youtube_analyzer
    participant C as config.py
    participant G as Gemini API
    participant V as Obsidian Vault

    U->>S: Ingresa URL Canal
    S->>A: get_video_list(url)
    A-->>S: Lista de Metadatos
    U->>S: Selecciona Videos
    loop Por cada video seleccionado
        S->>DB: has_been_processed(url)?
        alt Ya procesado
            S-->>U: ⏭️ Ya procesado
        else Nuevo
            S->>S: transcript_cache[id]?
            alt No está en caché
                S->>A: get_transcript(vid_id)
                A-->>S: (texto, idioma)
                S->>S: Guarda en transcript_cache
            end
            S->>PT: render_prompt("youtube_analysis", vars)
            PT-->>S: Prompt renderizado
            S->>C: generate_with_retry(prompt)
            C->>G: Prompt con transcripción
            G-->>C: Markdown Report
            C-->>S: Texto generado
            S->>V: save_note("10_YouTube/") → filepath
            S->>DB: record_ingestion('youtube', url, title, vault_path)
            S-->>U: Expander + ZIP descargable
        end
    end
```

---

## 2. Flujo de Auditoría GitHub

```mermaid
sequenceDiagram
    participant S as Streamlit App
    participant DB as knowledge.db
    participant GH as GitHub API
    participant GA as github_analyzer
    participant PT as prompts/github_wiki.md
    participant C as config.py
    participant G as Gemini API

    S->>GH: get_user_repos(user)
    GH-->>S: Lista de Repos
    loop Por cada repo seleccionado
        S->>DB: has_been_processed(url)?
        alt Ya procesado
            S-->>S: ⏭️ Ya procesado
        else Nuevo
            S->>GH: get_repo_structure(Trees API)
            GH-->>S: Full Tree JSON
            S->>GA: identify_critical_files(tree)
            GA-->>S: Hasta 12 File Paths (ADN)
            loop Por cada archivo crítico
                S->>GH: fetch_file_content(path)
                GH-->>S: Contenido decodificado (Base64)
            end
            S->>PT: render_prompt("github_wiki", vars)
            PT-->>S: Prompt renderizado
            S->>C: generate_with_retry(prompt)
            C->>G: Prompt con Tree + ADN
            G-->>C: Technical Wiki MD
            C-->>S: Texto generado
            S->>S: save_note("20_GitHub/")
            S->>DB: record_ingestion('github', url, name, vault_path)
        end
    end
```

---

## 3. Flujo de Ingesta Web

```mermaid
sequenceDiagram
    participant S as Streamlit App
    participant DB as knowledge.db
    participant W as web_analyzer
    participant PT as prompts/web_curation.md
    participant C as config.py
    participant G as Gemini API

    loop Por cada URL seleccionada
        S->>DB: has_been_processed(url)?
        alt Ya procesado
            S-->>S: ⏭️ Ya procesado
        else Nuevo
            S->>W: fetch_web_content(url)
            W->>W: requests.get + BeautifulSoup limpieza
            W-->>S: title + text[:15000]
            S->>PT: render_prompt("web_curation", vars)
            PT-->>S: Prompt renderizado
            S->>C: generate_with_retry(prompt)
            C->>G: Prompt Zettelkasten
            G-->>C: Nota MD estructurada
            C-->>S: Texto generado
            S->>S: save_note("30_Web/")
            S->>DB: record_ingestion('web', url, title, vault_path)
        end
    end
```

---

## 4. Flujo RSS Monitor

```mermaid
sequenceDiagram
    participant U as Usuario
    participant S as Streamlit App
    participant RM as rss_manager
    participant RDB as rss_feeds.db
    participant W as web_analyzer
    participant PT as prompts/rss_digest.md
    participant C as config.py
    participant V as Obsidian Vault

    U->>S: Agrega feed (nombre + URL)
    S->>RDB: add_feed(name, url)

    U->>S: "Revisar feeds ahora"
    S->>RDB: get_feeds()
    RDB-->>S: Lista de feeds

    loop Por cada feed
        S->>RM: fetch_new_articles(feed)
        RM->>RM: feedparser.parse(url)
        loop Por cada artículo nuevo
            RM->>W: fetch_web_content(entry.url)
            W-->>RM: Contenido limpio
            RM->>PT: render_prompt("rss_digest", vars)
            PT-->>RM: Prompt renderizado
            RM->>C: generate_with_retry(prompt)
            C-->>RM: Nota MD
            RM-->>V: save_note("30_Web/")
        end
    end
    S-->>U: Historial actualizado
```

---

## 5. Flujo NotebookLM Source Pack

```mermaid
sequenceDiagram
    participant U as Usuario
    participant S as Streamlit App
    participant NP as notebooklm_pack
    participant C as config.py
    participant G as Gemini API

    U->>S: Abre tab NotebookLM Pack
    S->>NP: Recopila fuentes de session_state
    NP-->>S: Lista: YT + GH + Web + RSS

    U->>S: "Generar Lista URLs"
    S->>NP: generate_source_list(all_results)
    NP-->>S: String con URLs (una por línea)
    S-->>U: Download "sources.txt"

    U->>S: "Generar Contexto Maestro"
    S->>NP: generate_context_markdown(all_results)
    NP->>C: generate_with_retry(prompt consolidado)
    C->>G: Resúmenes de todas las fuentes
    G-->>C: Nota MD de contexto enriquecida
    C-->>NP: Texto generado
    NP-->>S: Nota MD lista
    S-->>U: Download "context.md"
```

---

## 6. Flujo Analytics Dashboard

```mermaid
sequenceDiagram
    participant U as Usuario
    participant S as Streamlit App
    participant DB as knowledge.db

    U->>S: Abre tab Analytics
    S->>DB: get_ingestion_stats()
    DB-->>S: {total, success, failed, by_type, by_date, recent}
    S->>S: Renderiza KPI cards (total, éxito, fallos)
    S->>S: Renderiza bar chart por tipo de fuente
    S->>S: Renderiza line chart timeline (30 días)
    S->>S: Renderiza tabla de últimas 10 ingestas
    S-->>U: Dashboard renderizado

    opt Export
        U->>S: Click "Exportar CSV"
        S->>DB: list_recent_ingestions(limit=500)
        DB-->>S: Historial completo
        S-->>U: Download "ingestion_history.csv"
    end
```

---

## 7. Flujo de Prompt Rendering

```mermaid
flowchart LR
    A[Analyzer] --> B[Variables dict]
    B --> C[prompt_loader.render_prompt]
    C --> D[prompts/template.md]
    D --> E[Jinja2 render]
    E --> F[Prompt final string]
    F --> G[config.generate_with_retry]
    G --> H[Gemini API]
```

---

## 8. Flujo Audio/Podcast (Sprint 6 — Planeado)

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
    participant DB as knowledge.db

    alt Modo: Archivo subido
        U->>S: Sube .mp3/.wav/.m4a
        S->>AT: transcribe_bytes(audio_bytes)
        AT->>WH: model.transcribe(path)
        WH-->>AT: segments + idioma
        AT-->>S: (texto_completo, idioma)
        S->>PA: build_metadata_from_upload(filename)
    else Modo: URL de podcast
        U->>S: Ingresa URL feed o episodio
        S->>PA: detect_and_extract(url)
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
    S->>DB: record_ingestion('podcast', url, title, vault_path)
    S-->>U: Expander con nota + ZIP
```
