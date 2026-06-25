"""
services/tripo_ai.py
Integración con Tripo AI para generación de modelos 3D desde imagen.
API base: https://api.tripo3d.ai/v2/openapi

Flujo:
  1. analizar_imagen_con_claude()  → prompt 3D optimizado
  2. subir_imagen()                → image_token
  3. crear_tarea()                 → task_id
  4. consultar_estado()            → status / progress / output.model
  5. descargar_modelo()            → bytes del archivo 3D
  6. procesar_en_background()      → lanza worker en hilo separado
"""
import base64
import io
import logging
import os
import time

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

TRIPO_BASE_URL    = "https://api.tripo3d.ai/v2/openapi"
CLAUDE_MODEL      = "claude-sonnet-4-6"
POLLING_INTERVALO = 5    # segundos
TIMEOUT_MAXIMO    = 600  # 10 minutos

_TIPOS_MEDIA = {
    "jpg":  "image/jpeg",
    "jpeg": "image/jpeg",
    "png":  "image/png",
    "webp": "image/webp",
}


# ── Paso 1: Análisis con Claude ──────────────────────────────────────────────

def analizar_imagen_con_claude(imagen_bytes: bytes, extension: str) -> dict:
    """
    Analiza la imagen con Claude y retorna un dict con:
      DESCRIPCION, TIPO, PROMPT_3D, RECOMENDACIONES.
    Retorna {} si no hay API key o si falla.
    """
    api_key = getattr(settings, "ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY no configurada — análisis Claude omitido.")
        return {}

    try:
        import anthropic
        ext = extension.lower().lstrip(".")
        tipo_media = _TIPOS_MEDIA.get(ext, "image/jpeg")
        datos_b64  = base64.standard_b64encode(imagen_bytes).decode("utf-8")

        cliente   = anthropic.Anthropic(api_key=api_key)
        respuesta = cliente.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type":       "base64",
                                "media_type": tipo_media,
                                "data":       datos_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                "Analiza esta imagen para su conversión a modelo 3D. "
                                "Responde en este formato exacto:\n\n"
                                "DESCRIPCION: [descripción clara del objeto, máximo 2 oraciones]\n"
                                "TIPO: [logo | producto | personaje | edificio | objeto_simple | objeto_complejo]\n"
                                "PROMPT_3D: [prompt en inglés optimizado para 3D, máximo 30 palabras]\n"
                                "RECOMENDACIONES: [1-2 recomendaciones para mejorar el resultado 3D]\n\n"
                                "Sé preciso y técnico."
                            ),
                        },
                    ],
                }
            ],
        )

        texto     = respuesta.content[0].text
        resultado = {}
        for linea in texto.strip().split("\n"):
            if ":" in linea:
                clave, valor = linea.split(":", 1)
                resultado[clave.strip()] = valor.strip()
        return resultado

    except Exception as exc:
        logger.error("Error analizando imagen con Claude: %s", exc)
        return {}


# ── Paso 2a: Subir imagen a Tripo ────────────────────────────────────────────

def subir_imagen(imagen_bytes: bytes, extension: str, api_key: str) -> str:
    """
    Sube la imagen a Tripo AI.
    Retorna image_token.
    """
    ext = extension.lower().lstrip(".")
    if ext == "jpg":
        ext = "jpeg"
    tipo_media = _TIPOS_MEDIA.get(ext, "image/jpeg")

    headers  = {"Authorization": f"Bearer {api_key}"}
    respuesta = requests.post(
        f"{TRIPO_BASE_URL}/upload/sts",
        headers=headers,
        files={"file": (f"imagen.{ext}", io.BytesIO(imagen_bytes), tipo_media)},
        timeout=60,
    )
    respuesta.raise_for_status()
    datos = respuesta.json()
    if datos.get("code") != 0:
        raise ValueError(f"Tripo upload error (code={datos.get('code')}): {datos}")
    return datos["data"]["image_token"]


# ── Paso 2b: Crear tarea de generación ───────────────────────────────────────

def crear_tarea(image_token: str, extension: str, params: dict, api_key: str) -> str:
    """
    Crea una tarea image_to_model en Tripo AI.

    params admite:
      model_version, texture, pbr, face_limit,
      texture_alignment, orientation, enable_image_autofix, prompt

    Retorna task_id.
    """
    ext = extension.lower().lstrip(".")
    if ext == "jpg":
        ext = "jpeg"

    payload = {
        "type":         "image_to_model",
        "model_version": params.get("model_version", "P1-20260311"),
        "file": {
            "type":       ext,
            "file_token": image_token,
        },
        "texture":              params.get("texture",              True),
        "pbr":                  params.get("pbr",                  True),
        "face_limit":           params.get("face_limit",           20000),
        "texture_alignment":    params.get("texture_alignment",    "original_image"),
        "orientation":          params.get("orientation",          "align_image"),
        "enable_image_autofix": params.get("enable_image_autofix", True),
    }
    if params.get("prompt"):
        payload["prompt"] = params["prompt"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
    }
    respuesta = requests.post(
        f"{TRIPO_BASE_URL}/task",
        json=payload,
        headers=headers,
        timeout=30,
    )
    respuesta.raise_for_status()
    datos = respuesta.json()
    if datos.get("code") != 0:
        raise ValueError(f"Tripo task error (code={datos.get('code')}): {datos}")
    return datos["data"]["task_id"]


# ── Paso 3: Consultar estado ──────────────────────────────────────────────────

def consultar_estado(task_id: str, api_key: str) -> dict:
    """
    GET /task/{task_id}
    Retorna dict con: status, progress, output, task_error.
    """
    headers  = {"Authorization": f"Bearer {api_key}"}
    respuesta = requests.get(
        f"{TRIPO_BASE_URL}/task/{task_id}",
        headers=headers,
        timeout=30,
    )
    respuesta.raise_for_status()
    return respuesta.json().get("data", {})


# ── Paso 4: Descargar modelo ──────────────────────────────────────────────────

def descargar_modelo(url: str) -> bytes:
    """Descarga el archivo 3D desde la URL de Tripo AI y retorna sus bytes."""
    respuesta = requests.get(url, stream=True, timeout=120)
    respuesta.raise_for_status()
    buffer = io.BytesIO()
    for chunk in respuesta.iter_content(chunk_size=8192):
        buffer.write(chunk)
    return buffer.getvalue()


# ── Worker en segundo plano ───────────────────────────────────────────────────

def procesar_en_background(diseno_pk: int) -> None:
    """Lanza el polling + descarga en un hilo separado."""
    import threading
    hilo = threading.Thread(target=_worker, args=(diseno_pk,), daemon=True)
    hilo.start()


def _worker(diseno_pk: int) -> None:
    """
    Espera a que Tripo AI termine, descarga el modelo y actualiza Diseno3D.
    Se ejecuta en hilo separado; usa django.db.close_old_connections() al salir.
    """
    from django.core.files.base import ContentFile
    from django.db import close_old_connections

    # Importar modelo aquí para evitar circular imports
    from apps.produccion.models.diseno3d import Diseno3D

    api_key = getattr(settings, "TRIPO_API_KEY", os.getenv("TRIPO_API_KEY", ""))

    try:
        diseno   = Diseno3D.objects.get(pk=diseno_pk)
        task_id  = diseno.tripo_task_id
        if not task_id:
            logger.error("Diseno3D pk=%s no tiene task_id.", diseno_pk)
            return

        tiempo_inicio = time.time()
        while True:
            if time.time() - tiempo_inicio > TIMEOUT_MAXIMO:
                Diseno3D.objects.filter(pk=diseno_pk).update(
                    estado="fallido",
                    error_mensaje="Timeout: la generación superó los 10 minutos.",
                )
                return

            datos   = consultar_estado(task_id, api_key)
            estado  = datos.get("status", "unknown")
            progreso = datos.get("progress", 0)

            Diseno3D.objects.filter(pk=diseno_pk).update(progreso=progreso)

            if estado == "success":
                # Buscar URL del modelo en output
                output    = datos.get("output", {})
                url_modelo = output.get("model")
                if not url_modelo:
                    for v in output.values():
                        if isinstance(v, str) and v.startswith("http"):
                            url_modelo = v
                            break

                if not url_modelo:
                    Diseno3D.objects.filter(pk=diseno_pk).update(
                        estado="fallido",
                        error_mensaje="Tripo no retornó URL de descarga.",
                    )
                    return

                modelo_bytes   = descargar_modelo(url_modelo)
                diseno_obj     = Diseno3D.objects.get(pk=diseno_pk)
                nombre_archivo = f"modelo_{task_id}.{diseno_obj.formato}"
                diseno_obj.archivo_modelo.save(
                    nombre_archivo, ContentFile(modelo_bytes), save=False
                )
                Diseno3D.objects.filter(pk=diseno_pk).update(
                    estado="completado",
                    progreso=100,
                    url_descarga_tripo=url_modelo,
                    archivo_modelo=diseno_obj.archivo_modelo.name,
                )
                logger.info("Diseno3D pk=%s completado → %s", diseno_pk, nombre_archivo)
                return

            elif estado in ("failed", "cancelled"):
                error = datos.get("task_error", {})
                Diseno3D.objects.filter(pk=diseno_pk).update(
                    estado="fallido",
                    error_mensaje=error.get("message", f"Estado Tripo: {estado}"),
                )
                return

            time.sleep(POLLING_INTERVALO)

    except Exception as exc:
        logger.error("Error en worker Diseno3D pk=%s: %s", diseno_pk, exc)
        try:
            from apps.produccion.models.diseno3d import Diseno3D
            Diseno3D.objects.filter(pk=diseno_pk).update(
                estado="fallido",
                error_mensaje=str(exc)[:500],
            )
        except Exception:
            pass
    finally:
        close_old_connections()
