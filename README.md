# 🧠 Deep Audit Knowledge Engine

Ecosistema de agentes inteligentes para la ingesta de conocimiento desde YouTube, GitHub y la Web hacia Obsidian.

## 🚀 Inicio Rápido

1.  **Entorno**: Asegúrate de tener el entorno virtual activo.
    ```powershell
    .\venv\Scripts\activate
    ```
2.  **Ejecución**:
    ```powershell
    streamlit run app.py
    ```

## 🍳 Módulos Principales

### 1. 📺 YouTube Analysis
Auditoría técnica de videos. Extrae stack tecnológico, decisiones de arquitectura y resúmenes ejecutivos.

### 2. 👨‍🍳 Digital Chef (Nuevo)
Especializado en recetas de cocina.
-   **Entrada**: Soporta links de videos individuales o canales completos.
-   **Salida**: Notas en `50_Recetas` con formato Michelin (ingredientes, porciones, paso a paso).
-   **🛒 Lista del Súper**: Capacidad de consolidar múltiples recetas en una sola lista de compras categorizada.

### 3. 💻 GitHub Deep Audit
Analiza la estructura de repositorios, identifica archivos críticos y genera una Wiki estructurada.

### 4. 🌐 Web Ingestion
Convierte artículos y blogs en notas limpias para Obsidian.

### 5. 🧠 Obsidian Sync
Centraliza reportes de otros agentes de base de datos (`AuctionBot`, `DexScreener`, etc.) en notas diarias o individuales.

## 🛠️ Configuración (Sidebar)

-   **Ruta del Vault**: Define dónde se guardarán las notas. Por defecto: `C:\Users\luuis\Documents\Obsidian Vault\20_CONOCIMIENTO`.
-   **Auto-Save**: Si está activo, las notas se escriben directamente en el disco.

## ⚠️ Notas de Estabilidad (Cuotas de Gemini)

Este sistema utiliza el **Free Tier de Gemini 1.5 Flash**. 
-   **Límites**: 15 peticiones por minuto.
-   **Manejo de Errores**: Se ha implementado una lógica de **reintento automático**. Si recibes un error de "Cuota Agotada", la app esperará 30-60 segundos y reintentará el proceso por ti.

## 📁 Estructura de Carpetas en Obsidian

-   `10_YouTube`: Auditorías técnicas.
-   `20_GitHub`: Wikis de repositorios.
-   `30_Web`: Artículos web.
-   `50_Recetas`: Recetas y listas del súper.
-   `99_Sync`: Reportes de bots externos.

---
*Desarrollado con ❤️ por Antigravity para optimizar el cerebro digital.*
