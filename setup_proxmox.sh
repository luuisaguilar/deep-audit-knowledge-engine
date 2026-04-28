#!/bin/bash

# --- CONFIGURACIÓN ---
INSTALL_DIR="/root/youtube-analyzer"
SERVICE_NAME="youtube_service.service"

echo "🚀 Iniciando configuración de YouTube Analyzer 24/7..."

# 1. Actualizar sistema e instalar dependencias
apt update && apt install -y python3-pip python3-venv ffmpeg git

# 2. Crear directorio y clonar/copiar archivos
# Nota: Asumimos que los archivos ya están en el directorio o se copian manualmente
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# 3. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 4. Instalar dependencias de Python
pip install yt-dlp youtube-transcript-api google-generativeai streamlit pandas

# 5. Configurar el servicio systemd
echo "⚙️ Configurando servicio systemd..."
cp $INSTALL_DIR/$SERVICE_NAME /etc/systemd/system/
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

echo "✅ Instalación completada!"
echo "📍 El Dashboard debería estar corriendo en: http://$(hostname -I | awk '{print $1}'):8501"
echo "🔍 Revisa el estado con: systemctl status $SERVICE_NAME"
