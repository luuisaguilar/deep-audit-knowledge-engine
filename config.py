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


@retry(
    retry=retry_if_exception_type(exceptions.ResourceExhausted),
    wait=wait_exponential(multiplier=30, min=30, max=90),
    stop=stop_after_attempt(3),
    reraise=False,
)
def _generate_with_retry_internal(prompt: str) -> str:
    response = gemini_model.generate_content(prompt)
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
