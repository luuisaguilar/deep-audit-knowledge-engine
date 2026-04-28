import pandas as pd
from config import generate_with_retry


def analyze_cooking_video(video_data):
    """Analiza un video de cocina con el estilo de un Chef de alta cocina."""
    transcript = video_data.get('transcript', 'No disponible')

    prompt = f"""
Eres un Chef con Estrella Michelin experto en organización de cocina (mise en place).
Analiza la transcripción del video "{video_data.get('title', 'Receta')}" de {video_data.get('channel', 'Canal')}.

Tu objetivo es crear una nota de Obsidian PERFECTA con el siguiente formato Markdown:

---
tipo: receta
fuente: "{video_data.get('url', 'N/A')}"
canal: "{video_data.get('channel', 'N/A')}"
dificultad: [baja/media/alta]
tiempo_estimado: [X minutos]
porciones: [Número de personas]
---

# 🍳 {video_data.get('title', 'Receta')}

## 📋 Ingredientes
(Lista detallada con cantidades exactas. Agrupa por componentes si es necesario, ej: 'Para la salsa', 'Para la masa')

## 🔪 Utensilios Necesarios
(Lista de herramientas clave mencionadas)

## 👨‍🍳 Procedimiento (Paso a Paso)
(Instrucciones claras, numeradas y profesionales. No saltes ningún detalle del proceso)

## 💡 Tips del Chef
(Consejos sobre técnica, sustitutos o secretos que se mencionen en el video)

Transcripción:
{transcript}

IMPORTANTE: No uses términos técnicos de software (ej: 'tech stack', 'architecture').
Usa lenguaje culinario. Si no se mencionan porciones, estima según los ingredientes.
"""

    return generate_with_retry(prompt)


def generate_grocery_list(recipes_content_list):
    """Genera una lista de compras consolidada a partir de varias recetas."""
    combined_content = "\n\n---\n\n".join(recipes_content_list)

    prompt = f"""
Eres un experto en logística de banquetes. Consolida estos ingredientes en una nota de compras.

Formato:
# 🛒 Lista de Compras Consolidada ({pd.Timestamp.now().strftime('%Y-%m-%d')})

## 🥦 Verduras y Frutas
## 🥩 Carnes y Proteínas
## 🥛 Lácteos y Refrigerados
## 🧂 Despensa y Especias
## 🥖 Otros

Contenido:
{combined_content}
"""

    return generate_with_retry(prompt)
