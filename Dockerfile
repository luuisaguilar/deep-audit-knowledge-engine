# Usar una imagen ligera de Python
FROM python:3.11-slim

# Evitar que Python genere archivos .pyc y permitir que los logs lleguen al terminal inmediatamente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema (ffmpeg es crítico, nodejs requerido por yt-dlp)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar dependencias de Playwright para DocGrab
RUN playwright install-deps
RUN playwright install chromium

# Copiar el resto del código
COPY . .

# Exponer el puerto de Streamlit
EXPOSE 8501

# Comando para arrancar la aplicación
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false"]
