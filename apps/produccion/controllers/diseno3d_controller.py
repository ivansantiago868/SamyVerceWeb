"""
controllers/diseno3d_controller.py
Orquesta la generación de modelos 3D: Claude → Tripo upload → Tripo task → polling worker.
"""
import logging
import os

from django.conf import settings

logger = logging.getLogger(__name__)


class Diseno3DController:

    @staticmethod
    def iniciar_generacion(diseno) -> None:
        """
        1. Lee la imagen del campo ImageField.
        2. Analiza con Claude (si hay ANTHROPIC_API_KEY).
        3. Sube la imagen a Tripo AI → image_token.
        4. Crea la tarea Tripo AI → task_id.
        5. Persiste task_id + analisis_ia + prompt en DB.
        6. Lanza worker de polling en hilo separado.

        Lanza ValueError si TRIPO_API_KEY no está configurada o si Tripo falla.
        """
        from apps.produccion.models.diseno3d import Diseno3D
        from apps.produccion.services import tripo_ai

        api_key = getattr(settings, "TRIPO_API_KEY", os.getenv("TRIPO_API_KEY", ""))
        if not api_key:
            raise ValueError(
                "TRIPO_API_KEY no está configurada. "
                "Agrégala en .env y en config/settings/base.py."
            )

        # Leer bytes de la imagen
        imagen_field = diseno.imagen_original
        extension    = imagen_field.name.split(".")[-1].lower()

        try:
            imagen_field.seek(0)
            imagen_bytes = imagen_field.read()
        except Exception:
            try:
                with imagen_field.open("rb") as f:
                    imagen_bytes = f.read()
            except Exception:
                import requests as _r
                resp = _r.get(imagen_field.url, timeout=30)
                resp.raise_for_status()
                imagen_bytes = resp.content

        # Análisis con Claude (no bloquea si falla)
        analisis = tripo_ai.analizar_imagen_con_claude(imagen_bytes, extension)

        # Prompt: usa el del usuario si existe, sino el de Claude
        prompt = diseno.prompt or analisis.get("PROMPT_3D", "")

        # Subir imagen a Tripo
        image_token = tripo_ai.subir_imagen(imagen_bytes, extension, api_key)

        # Crear tarea en Tripo con todos los parámetros del modelo
        params = {
            "model_version":        diseno.model_version,
            "texture":              diseno.texture,
            "pbr":                  diseno.pbr,
            "face_limit":           diseno.face_limit,
            "texture_alignment":    diseno.texture_alignment,
            "orientation":          diseno.orientation,
            "enable_image_autofix": diseno.enable_image_autofix,
            "prompt":               prompt,
        }
        task_id = tripo_ai.crear_tarea(image_token, extension, params, api_key)

        # Persistir resultados iniciales
        Diseno3D.objects.filter(pk=diseno.pk).update(
            tripo_task_id=task_id,
            tripo_image_token=image_token,
            analisis_ia=analisis,
            prompt=prompt,
            estado="procesando",
            progreso=0,
        )

        # Lanzar polling en segundo plano
        tripo_ai.procesar_en_background(diseno.pk)
        logger.info("Diseno3D pk=%s — tarea Tripo iniciada: %s", diseno.pk, task_id)

    @staticmethod
    def get_estado(diseno_pk: int, empresa=None) -> dict:
        """
        Retorna estado actual del diseño 3D.
        Levanta LookupError si no existe o no pertenece a la empresa.
        """
        from apps.produccion.models.diseno3d import Diseno3D

        qs = Diseno3D.objects.filter(pk=diseno_pk)
        if empresa:
            qs = qs.filter(empresa=empresa)
        diseno = qs.first()
        if not diseno:
            raise LookupError(f"Diseño 3D #{diseno_pk} no encontrado.")

        resultado = {
            "id":             diseno.pk,
            "nombre":         diseno.nombre,
            "estado":         diseno.estado,
            "progreso":       diseno.progreso,
            "error_mensaje":  diseno.error_mensaje,
            "tripo_task_id":  diseno.tripo_task_id,
            "analisis_ia":    diseno.analisis_ia,
            "creado_en":      diseno.creado_en.isoformat(),
            "actualizado_en": diseno.actualizado_en.isoformat(),
        }
        if diseno.estado == "completado" and diseno.archivo_modelo:
            try:
                resultado["url_modelo"] = diseno.archivo_modelo.url
            except Exception:
                resultado["url_modelo"] = None
        return resultado
