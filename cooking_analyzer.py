import pandas as pd
from config import generate_with_retry
from core.prompt_loader import render_prompt


def analyze_cooking_video(video_data):
    """Analiza un video de cocina con el estilo de un Chef de alta cocina."""
    prompt = render_prompt("cooking_recipe", {
        "title": video_data.get('title', 'Receta'),
        "channel": video_data.get('channel', 'Canal'),
        "url": video_data.get('url', 'N/A'),
        "transcript": video_data.get('transcript', 'No disponible'),
    })

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
