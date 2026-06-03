"""
Procesamiento de imágenes de producto con Google Imagen via google-genai SDK.
Modelo: imagen-3.0-edit-001 | Modo: EDIT_MODE_PRODUCT_IMAGE

Configuración requerida en .env:
    GEMINI_API_KEY = tu-api-key-de-google-ai-studio
"""
import io
import logging
import os
import ssl
import time

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import connection
from google import genai
from google.genai import types
from PIL import Image

_MODELO_IMAGEN = "gemini-2.5-flash-image"
_MODELO_TEXTO  = "gemini-2.5-flash"

logger = logging.getLogger(__name__)

_PROMPT_ESTUDIO = (
    "Minimalist product photography in a studio setting. The subject is placed on a smooth, "
    "matte white tabletop with a clean white backdrop, but with a subtle visible horizon line "
    "where the background meets the surface. The transition between wall and table is soft but "
    "perceptible, adding depth.\n"
    "Soft, diffused lighting from one side (left or slightly above-left), creating gentle shadows "
    "and a light gradient across the background. Slight shadow falloff near the base of the product "
    "to enhance grounding. High-key aesthetic with controlled contrast, no harsh reflections, and "
    "smooth tonal transitions.\n"
    "Camera angle is slightly low and front-facing (around 10–20 degrees above the surface), "
    "emphasizing volume and depth. Composition is centered or slightly off-center with generous "
    "negative space. The product is in sharp focus with crisp detail, while the background remains "
    "clean and minimal.\n"
    "Neutral color palette, modern editorial style. No props or distractions—focus on shape, "
    "texture, and silhouette. Ultra clean studio product shot."
)

_MAX_PX  = 1200
_QUALITY = 88


_REINTENTOS = 4
_ESPERA_BASE = 2  # segundos (2 → 4 → 8 → 16)
_ERRORES_REINTENTABLES = (
    ssl.SSLError,
    ConnectionError,
    TimeoutError,
)


def _descargar_url(url: str) -> bytes | None:
    """Descarga una URL con reintentos ante errores SSL o de red transitorios."""
    import requests as _req
    for intento in range(1, _REINTENTOS + 1):
        try:
            r = _req.get(url, timeout=20)
            r.raise_for_status()
            return r.content
        except _ERRORES_REINTENTABLES as exc:
            espera = _ESPERA_BASE ** intento
            logger.warning(
                "Descarga fallida (intento %d/%d) — %s — reintentando en %ds",
                intento, _REINTENTOS, exc, espera,
            )
            time.sleep(espera)
        except Exception as exc:
            logger.error("Error descargando imagen %s: %s", url, exc)
            return None
    logger.error("No se pudo descargar %s tras %d intentos.", url, _REINTENTOS)
    return None


def procesar_imagen_estudio(ruta: str) -> bytes | None:
    """
    Edita la imagen del producto con Imagen 3 via Google AI Studio API key.
    Retorna bytes JPEG listos para guardar, o None si falla.
    """
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key:
        logger.warning("GEMINI_API_KEY no configurada — procesamiento omitido.")
        return None

    try:
        client = genai.Client(api_key=api_key)

        if ruta.startswith("http://") or ruta.startswith("https://"):
            img_bytes = _descargar_url(ruta)
            if img_bytes is None:
                return None
        else:
            with open(ruta, "rb") as f:
                img_bytes = f.read()

        respuesta = client.models.generate_content(
            model=_MODELO_IMAGEN,
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                types.Part.from_text(text=_PROMPT_ESTUDIO),
            ],
            config=types.GenerateContentConfig(
                response_modalities=["image"],
            ),
        )

        imagen_bytes = None
        for part in respuesta.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                imagen_bytes = part.inline_data.data
                break

        if not imagen_bytes:
            logger.error("Gemini no retornó imagen.")
            return None

        img = Image.open(io.BytesIO(imagen_bytes)).convert("RGB")
        img.thumbnail((_MAX_PX, _MAX_PX), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=_QUALITY, optimize=True)
        return buf.getvalue()

    except Exception as exc:
        msg = str(exc)
        if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
            logger.warning(
                "Gemini API: cupo agotado (modelo de pago). "
                "Activa facturación en console.cloud.google.com/billing"
            )
        elif "API_KEY_INVALID" in msg or "400" in msg:
            logger.error("Gemini API: clave inválida — verifica GEMINI_API_KEY en .env")
        else:
            logger.error("Gemini API exception: %s", msg[:200])
        return None


def _procesar(model_class, pk: int, ruta: str) -> None:
    """Lógica de procesamiento pura — sin manejo de conexión ni hilos."""
    for intento in range(1, _REINTENTOS + 1):
        try:
            resultado = procesar_imagen_estudio(ruta)
            if not resultado:
                return
            base   = os.path.splitext(os.path.basename(ruta))[0]
            nombre = f"{base}_studio.jpg"
            obj    = model_class.objects.get(pk=pk)
            obj.imagen_procesada.save(nombre, ContentFile(resultado), save=False)
            model_class.objects.filter(pk=pk).update(imagen_procesada=obj.imagen_procesada.name)
            logger.info("Imagen procesada: %s id=%s → %s", model_class.__name__, pk, nombre)
            return
        except ssl.SSLError as exc:
            espera = _ESPERA_BASE ** intento
            if intento < _REINTENTOS:
                logger.debug(
                    "SSL transitorio %s id=%s (intento %d/%d) — reintentando en %ds",
                    model_class.__name__, pk, intento, _REINTENTOS, espera,
                )
                time.sleep(espera)
            else:
                logger.warning(
                    "SSL persistente %s id=%s tras %d intentos: %s",
                    model_class.__name__, pk, _REINTENTOS, exc,
                )
        except Exception as exc:
            espera = _ESPERA_BASE ** intento
            if intento < _REINTENTOS:
                logger.warning(
                    "Error procesando %s id=%s (intento %d/%d): %s — reintentando en %ds",
                    model_class.__name__, pk, intento, _REINTENTOS, exc, espera,
                )
                time.sleep(espera)
            else:
                logger.error(
                    "Fallo definitivo %s id=%s tras %d intentos: %s",
                    model_class.__name__, pk, _REINTENTOS, exc,
                )


def procesar_en_background(model_class, pk: int, ruta: str) -> None:
    """Procesa la imagen de forma síncrona — bloquea hasta terminar."""
    try:
        _procesar(model_class, pk, ruta)
    except Exception as exc:
        logger.error("Error inesperado procesando %s id=%s: %s", model_class.__name__, pk, exc)
