import requests
import base64
from config import GITHUB_TOKEN, generate_with_retry

HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}


def get_user_repos(username):
    """Obtiene la lista de repositorios de un usuario. Soporta URLs completas."""
    if "github.com/" in username:
        username = username.split("github.com/")[-1].strip("/")

    url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=50"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        raise Exception(f"GitHub API Error: {resp.json().get('message', 'Unknown error')}")

    repos = []
    for r in resp.json():
        repos.append({
            'name': r['name'],
            'full_name': r['full_name'],
            'description': r.get('description', ''),
            'language': r.get('language', 'N/A'),
            'stars': r.get('stargazers_count', 0),
            'url': r['html_url'],
            'owner': r['owner']['login'],
            'default_branch': r.get('default_branch', 'main')
        })
    return repos


def get_repo_structure(owner, repo, branch='main'):
    """Obtiene el árbol de archivos (recursivo) usando la rama correcta."""
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        return []
    return [item['path'] for item in resp.json().get('tree', []) if item.get('type') == 'blob']


def fetch_file_content(owner, repo, path):
    """Descarga el contenido de un archivo específico."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        data = resp.json()
        if isinstance(data, dict):
            content_b64 = data.get('content', '')
            return base64.b64decode(content_b64).decode('utf-8', errors='ignore')
    return None


def identify_critical_files(file_list):
    """Identifica los archivos más importantes con patrones refinados."""
    high_priority = [
        'README.md', 'package.json', 'requirements.txt', 'docker-compose.yml', 'docker-compose.yaml',
        'schema.prisma', 'go.mod', 'cargo.toml', 'pyproject.toml', 'gemfile', 'composer.json'
    ]
    logic_patterns = ['routes/', 'api/', 'models/', 'controllers/', 'src/app.']

    selected = []
    for path in file_list:
        filename = path.split('/')[-1].lower()
        if filename in [p.lower() for p in high_priority]:
            selected.append(path)

    for path in file_list:
        if len(selected) >= 12:
            break
        if any(pat in path.lower() for pat in logic_patterns):
            if path not in selected and 'node_modules' not in path and 'vendor' not in path:
                selected.append(path)

    return selected[:12]


def analyze_repository_wiki(_owner, repo, repo_info, file_structure, files_data):
    """Genera la Wiki técnica con Gemini."""
    if not files_data:
        return "⚠️ Error: No se pudieron extraer archivos críticos para el análisis técnico."

    context = (
        f"Repositorio: {repo_info['full_name']}\n"
        f"Descripción: {repo_info['description']}\n"
        f"Rama Principal: {repo_info.get('default_branch', 'N/A')}\n"
        f"Lenguaje Principal: {repo_info['language']}\n"
        f"Estructura de Archivos (Muestra): {', '.join(file_structure[:40])}\n\n"
    )
    for path, content in files_data.items():
        context += f"--- ARCHIVO: {path} ---\n{content[:4000]}\n\n"

    prompt = (
        "Actúa como un CTO y Arquitecto de Software Senior. Genera una WIKI TÉCNICA detallada formateada para Obsidian.\n\n"
        "REQUISITO CRÍTICO: Comienza SIEMPRE con un bloque YAML Properties exactamente así:\n"
        "---\n"
        "tipo: repo_audit\n"
        f"repo: \"{repo_info['full_name']}\"\n"
        f"stack: \"{repo_info['language']}\"\n"
        f"stars: {repo_info['stars']}\n"
        "estado: auditado\n"
        "---\n\n"
        f"# Wiki Técnica: {repo}\n\n"
        "Si el README o el código sugieren idioma español, redacta en ESPAÑOL. De lo contrario, en INGLÉS.\n\n"
        "SECCIONES REQUERIDAS:\n"
        "1. **Tech Stack & Tools**: Frameworks, lenguajes, DBs.\n"
        "2. **Arquitectura & Estructura**: Flujo del proyecto y carpetas.\n"
        "3. **Modelado de Datos**: Tablas o entidades.\n"
        "4. **Lógica Principal**: Procesos clave.\n"
        "5. **Conclusiones de Auditoría**: Fortalezas técnicas.\n\n"
        f"CONTENIDO TÉCNICO:\n{context}"
    )

    return generate_with_retry(prompt)
