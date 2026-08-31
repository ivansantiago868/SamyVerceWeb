from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from .empresa import Empresa


class Cliente(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True, related_name="clientes", verbose_name="Empresa")
    categorias_visibles = models.ManyToManyField(
        "produccion.CategoriaFigura", blank=True, related_name="clientes_visibles",
        verbose_name="Categorías visibles para este cliente",
        help_text="Catálogo público (enlace con ?cliente=): si no eliges ninguna, se muestran todas las categorías.",
    )
    password = models.CharField(
        max_length=128, blank=True, verbose_name="Contraseña (portal del cliente)",
        help_text="Hash de la contraseña de acceso al portal del catálogo. Se define desde el formulario de edición.",
    )

    class TipoDocumento(models.TextChoices):
        CC  = "CC",  "Cédula de Ciudadanía"
        PPT = "PPT", "Permiso de Protección Temporal"
        NIT = "NIT", "NIT"
        CE  = "CE",  "Cédula Extranjería"
        PAS = "PAS", "Pasaporte"

    nombre         = models.CharField(max_length=255, verbose_name="Nombre / Razón social")
    tipo_documento = models.CharField(max_length=5, choices=TipoDocumento.choices, blank=True)
    documento      = models.CharField(max_length=30, blank=True, verbose_name="Número de documento")
    email          = models.EmailField(blank=True)
    telefono       = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    direccion      = models.TextField(blank=True, verbose_name="Dirección")
    comision       = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Comisión (%)",
        help_text="Porcentaje de comisión asociado a este cliente.",
    )
    notas          = models.TextField(blank=True)
    creado_en      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering        = ["nombre"]
        verbose_name    = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return self.nombre
