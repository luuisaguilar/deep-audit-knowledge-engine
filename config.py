import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core import exceptions
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY no encontrada. Asegúrate de tener un archivo .env con la clave.")

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

class TokenTracker:
    def __init__(self):
        self.prompt_tokens = 0
        self.completion_tokens = 0

    def add(self, p, c):
        self.prompt_tokens += p
        self.completion_tokens += c

    def get_and_reset(self):
        """Returns current tokens and resets the counter for the next ingestion."""
        res = (self.prompt_tokens, self.completion_tokens)
        self.prompt_tokens = 0
        self.completion_tokens = 0
        return res

token_tracker = TokenTracker()


@retry(
    retry=retry_if_exception_type(exceptions.ResourceExhausted),
    wait=wait_exponential(multiplier=30, min=30, max=90),
    stop=stop_after_attempt(3),
    reraise=False,
)
def _generate_with_retry_internal(prompt: str) -> str:
    response = gemini_model.generate_content(prompt)
    if hasattr(response, 'usage_metadata'):
        token_tracker.add(
            response.usage_metadata.prompt_token_count,
            response.usage_metadata.candidates_token_count
        )
    return response.text


def generate_with_retry(prompt: str) -> str:
    """Llama a Gemini con reintentos automáticos ante errores de cuota.

    Devuelve el texto generado, o un string con prefijo '⚠️ ERROR' si falla.
    """
    try:
        return _generate_with_retry_internal(prompt)
    except exceptions.ResourceExhausted:
        return "⚠️ ERROR: Cuota de Gemini agotada después de varios intentos. Espera unos minutos."
    except Exception as e:
        return f"⚠️ ERROR INESPERADO: {str(e)}"

@retry(
    retry=retry_if_exception_type(exceptions.ResourceExhausted),
    wait=wait_exponential(multiplier=30, min=30, max=90),
    stop=stop_after_attempt(3),
    reraise=False,
)
def _generate_with_media_retry_internal(prompt: str, media_file) -> str:
    response = gemini_model.generate_content([prompt, media_file])
    if hasattr(response, 'usage_metadata'):
        token_tracker.add(
            response.usage_metadata.prompt_token_count,
            response.usage_metadata.candidates_token_count
        )
    return response.text

def generate_with_media_retry(prompt: str, media_path: str, mime_type: str = None) -> str:
    """Sube un archivo a Gemini, genera contenido y limpia el archivo."""
    try:
        # Sube el archivo a los servidores de Gemini temporalmente
        uploaded_file = genai.upload_file(path=media_path, mime_type=mime_type)
        
        try:
            # Llama a la generación con reintentos
            result = _generate_with_media_retry_internal(prompt, uploaded_file)
            return result
        finally:
            # Limpieza: borrar el archivo de los servidores de Google
            try:
                genai.delete_file(uploaded_file.name)
            except Exception as cleanup_error:
                print(f"Error limpiando archivo en Gemini: {cleanup_error}")

    except exceptions.ResourceExhausted:
        return "⚠️ ERROR: Cuota de Gemini agotada después de varios intentos."
    except Exception as e:
        return f"⚠️ ERROR INESPERADO: {str(e)}"

def generate_embedding(text: str) -> list[float]:
    """Genera un vector embedding para el texto usando Gemini."""
    try:
        # Usamos el modelo más reciente para embeddings de texto
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"Error generando embedding: {e}")
        return []
