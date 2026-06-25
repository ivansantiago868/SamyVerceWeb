from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .empresa import Empresa


class Diseno3D(models.Model):
    ESTADO = [
        ("pendiente",  "Pendiente"),
        ("procesando", "Procesando"),
        ("completado", "Completado"),
        ("fallido",    "Fallido"),
    ]
    FORMATOS = [
        ("glb",  "GLB (recomendado)"),
        ("fbx",  "FBX"),
        ("obj",  "OBJ"),
        ("stl",  "STL"),
        ("usdz", "USDZ"),
    ]
    ORIENTACIONES = [
        ("align_image", "Alinear con imagen"),
        ("default",     "Por defecto"),
    ]
    TEXTURE_ALIGN = [
        ("original_image", "Imagen original"),
        ("geometry",       "Geometría"),
    ]

    empresa  = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True,
                                 related_name="disenos_3d", verbose_name="Empresa")
    usuario  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name="Usuario")
    nombre   = models.CharField(max_length=255, blank=True, verbose_name="Nombre")

    # ── Imagen de entrada ─────────────────────────────────────────────
    imagen_original = models.ImageField(
        upload_to="disenos3d/imagenes/", verbose_name="Imagen de referencia"
    )

    # ── Parámetros Tripo AI ───────────────────────────────────────────
    model_version        = models.CharField(max_length=50, default="P1-20260311",
                                            verbose_name="Versión del modelo")
    formato              = models.CharField(max_length=10, choices=FORMATOS, default="glb",
                                            verbose_name="Formato de salida")
    texture              = models.BooleanField(default=True,  verbose_name="Textura")
    pbr                  = models.BooleanField(default=True,  verbose_name="PBR (físicamente realista)")
    face_limit           = models.PositiveIntegerField(default=20000,
                                                        verbose_name="Límite de polígonos")
    texture_alignment    = models.CharField(max_length=30, choices=TEXTURE_ALIGN,
                                            default="original_image",
                                            verbose_name="Alineación de textura")
    orientation          = models.CharField(max_length=30, choices=ORIENTACIONES,
                                            default="align_image",
                                            verbose_name="Orientación")
    enable_image_autofix = models.BooleanField(default=True,
                                               verbose_name="Corrección automática de imagen")
    prompt               = models.TextField(blank=True, verbose_name="Prompt (descripción 3D)")

    # ── Análisis Claude ───────────────────────────────────────────────
    analisis_ia = models.JSONField(null=True, blank=True, verbose_name="Análisis Claude")

    # ── Estado del proceso ────────────────────────────────────────────
    tripo_task_id     = models.CharField(max_length=120, blank=True,
                                         verbose_name="ID de tarea Tripo")
    tripo_image_token = models.CharField(max_length=300, blank=True,
                                         verbose_name="Token imagen Tripo")
    estado            = models.CharField(max_length=20, choices=ESTADO, default="pendiente",
                                         verbose_name="Estado", db_index=True)
    progreso          = models.PositiveSmallIntegerField(default=0, verbose_name="Progreso (%)")
    error_mensaje     = models.TextField(blank=True, verbose_name="Error")

    # ── Resultado ─────────────────────────────────────────────────────
    archivo_modelo     = models.FileField(upload_to="disenos3d/modelos/", null=True, blank=True,
                                          verbose_name="Modelo 3D")
    url_descarga_tripo = models.URLField(max_length=500, blank=True,
                                         verbose_name="URL descarga Tripo")

    creado_en      = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering            = ["-creado_en"]
        verbose_name        = "Diseño 3D"
        verbose_name_plural = "Diseños 3D"

    def __str__(self):
        return self.nombre or f"Diseño 3D #{self.pk}"


def _borrar_campo(field):
    if not field or not field.name:
        return
    if "/" not in field.name and "." not in field.name:
        # Google Drive ID — usa storage
        try:
            field.storage.delete(field.name)
        except Exception:
            pass
    else:
        try:
            field.storage.delete(field.name)
        except Exception:
            pass


@receiver(post_delete, sender=Diseno3D)
def borrar_archivos_diseno3d(sender, instance, **kwargs):
    _borrar_campo(instance.imagen_original)
    _borrar_campo(instance.archivo_modelo)
