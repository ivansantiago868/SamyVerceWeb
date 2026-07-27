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
    "Minimalist studio product photography. The product is the absolute main subject and must "
    "fill 80–90% of the frame — close-up, tight crop, no wide shots. Do NOT place the product "
    "far away or small. The product must appear large, near and prominent.\n"
    "Background: smooth matte white surface with a clean white backdrop. Subtle soft horizon line "
    "where wall meets table, adding just a hint of depth. Keep background simple and uncluttered.\n"
    "Lighting: soft diffused light from slightly above-left, gentle shadow at the base to ground "
    "the product. High-key, no harsh reflections, smooth tonal transitions.\n"
    "Camera: front-facing, slightly above eye level (10–15 degrees), product centered. "
    "Minimal padding around the product — just enough breathing room (5–10% margin on each side). "
    "The product must be in sharp focus with crisp detail.\n"
    "Neutral color palette, modern editorial style. No props, no distractions. "
    "Ultra clean close-up studio product shot."
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


def procesar_imagen_estudio(ruta: str) -> tuple[bytes | None, str | None]:
    """
    Edita la imagen del producto con Imagen 3 via Google AI Studio API key.
    Retorna (bytes JPEG listos para guardar, None) o (None, mensaje_de_error).
    """
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key:
        mensaje = "GEMINI_API_KEY no configurada — procesamiento omitido."
        logger.warning(mensaje)
        return None, mensaje

    try:
        client = genai.Client(api_key=api_key)

        if ruta.startswith("http://") or ruta.startswith("https://"):
            img_bytes = _descargar_url(ruta)
            if img_bytes is None:
                return None, f"No se pudo descargar la imagen original desde {ruta}"
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
            mensaje = "Gemini no retornó ninguna imagen en la respuesta."
            logger.error(mensaje)
            return None, mensaje

        img = Image.open(io.BytesIO(imagen_bytes)).convert("RGB")
        img.thumbnail((_MAX_PX, _MAX_PX), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=_QUALITY, optimize=True)
        return buf.getvalue(), None

    except Exception as exc:
        msg = str(exc)
        if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
            mensaje = (
                "Gemini API: cupo agotado (modelo de pago). "
                "Activa facturación en console.cloud.google.com/billing"
            )
            logger.warning(mensaje)
        elif "API_KEY_INVALID" in msg or "400" in msg:
            mensaje = "Gemini API: clave inválida — verifica GEMINI_API_KEY en .env"
            logger.error(mensaje)
        else:
            mensaje = f"Gemini API exception: {msg[:300]}"
            logger.error(mensaje)
        return None, mensaje


def _guardar_error(model_class, pk: int, mensaje: str) -> None:
    """Persiste el motivo del fallo en ia_error para que sea visible en el admin."""
    try:
        model_class.objects.filter(pk=pk).update(ia_error=(mensaje or "")[:500])
    except Exception:
        logger.exception("No se pudo guardar ia_error para %s id=%s", model_class.__name__, pk)


def _procesar(model_class, pk: int, ruta: str) -> None:
    """Lógica de procesamiento pura — sin manejo de conexión ni hilos."""
    for intento in range(1, _REINTENTOS + 1):
        try:
            resultado, error_msg = procesar_imagen_estudio(ruta)
            if not resultado:
                _guardar_error(model_class, pk, error_msg or "Gemini no devolvió una imagen procesada.")
                return
            base   = os.path.splitext(os.path.basename(ruta))[0]
            nombre = f"{base}_studio.jpg"
            obj    = model_class.objects.get(pk=pk)
            storage_anterior = obj.imagen_procesada.storage
            nombre_anterior  = obj.imagen_procesada.name
            obj.imagen_procesada.save(nombre, ContentFile(resultado), save=False)
            model_class.objects.filter(pk=pk).update(imagen_procesada=obj.imagen_procesada.name, ia_error="")
            if nombre_anterior and nombre_anterior != obj.imagen_procesada.name:
                from types import SimpleNamespace
                from config.google_drive_storage import borrar_archivo_drive
                borrar_archivo_drive(SimpleNamespace(name=nombre_anterior, storage=storage_anterior))
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
                _guardar_error(model_class, pk, f"Error de red persistente tras {_REINTENTOS} intentos: {exc}")
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
                _guardar_error(model_class, pk, f"Fallo tras {_REINTENTOS} intentos: {exc}")


def procesar_en_background(model_class, pk: int, ruta: str) -> None:
    """Lanza el procesamiento en un hilo separado para no bloquear el request."""
    import threading
    hilo = threading.Thread(target=_worker, args=(model_class, pk, ruta), daemon=True)
    hilo.start()


def _worker(model_class, pk: int, ruta: str) -> None:
    """Ejecuta _procesar() en el hilo y cierra la conexión de BD al salir."""
    from django.db import close_old_connections
    try:
        _procesar(model_class, pk, ruta)
    except Exception as exc:
        logger.error("Error inesperado procesando %s id=%s: %s", model_class.__name__, pk, exc)
        _guardar_error(model_class, pk, f"Error inesperado: {exc}")
    finally:
        close_old_connections()
