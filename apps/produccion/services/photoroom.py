import io
import logging

import requests
from django.conf import settings
from PIL import Image

logger = logging.getLogger(__name__)

_PROMPT_ESTUDIO = (
    "Minimalist product photography in a studio setting. The subject is placed on a smooth, "
    "matte white tabletop with a clean white backdrop, but with a subtle visible horizon line "
    "where the background meets the surface. The transition between wall and table is soft but "
    "perceptible, adding depth. "
    "Soft, diffused lighting from one side (left or slightly above-left), creating gentle shadows "
    "and a light gradient across the background. Slight shadow falloff near the base of the product "
    "to enhance grounding. High-key aesthetic with controlled contrast, no harsh reflections, and "
    "smooth tonal transitions. "
    "Camera angle is slightly low and front-facing (around 10–20 degrees above the surface), "
    "emphasizing volume and depth. Composition is centered or slightly off-center with generous "
    "negative space. The product is in sharp focus with crisp detail, while the background remains "
    "clean and minimal. "
    "Neutral color palette, modern editorial style. No props or distractions—focus on shape, "
    "texture, and silhouette. Ultra clean studio product shot."
)

_MAX_PX   = 1200   # lado máximo de la imagen resultante
_QUALITY  = 88     # calidad JPEG de salida


def procesar_imagen_estudio(ruta: str) -> bytes | None:
    """
    Envía la imagen en `ruta` a Photoroom API y retorna JPEG procesado.
    — Fondo de estudio generado por IA (prompt de producto minimalista).
    — Mantiene proporciones originales (sin recorte forzado).
    — Redimensiona a máximo 1200 px y convierte a JPEG para ahorrar espacio.
    Retorna None si no hay API key o si la llamada falla.
    """
    api_key = getattr(settings, "PHOTOROOM_API_KEY", "")
    if not api_key:
        logger.warning("PHOTOROOM_API_KEY no configurada — procesamiento omitido.")
        return None

    try:
        with open(ruta, "rb") as f:
            resp = requests.post(
                "https://image-api.photoroom.com/v2/edit",
                headers={"x-api-key": api_key},
                files={"imageFile": ("imagen.jpg", f, "image/jpeg")},
                data={
                    "background.prompt": _PROMPT_ESTUDIO,
                    "padding":           "0.08",
                },
                timeout=60,
            )

        if resp.status_code != 200:
            logger.error("Photoroom API %s: %s", resp.status_code, resp.text[:300])
            return None

        # Redimensionar manteniendo proporción y convertir a JPEG
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        img.thumbnail((_MAX_PX, _MAX_PX), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=_QUALITY, optimize=True)
        return buf.getvalue()

    except Exception as exc:
        logger.error("Photoroom API exception: %s", exc)
        return None
