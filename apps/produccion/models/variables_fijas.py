from django.db import models
from django.core.validators import MinValueValidator


class VariablesFijas(models.Model):
    """
    Singleton: siempre existe un solo registro con pk=1.
    Contiene todos los parámetros globales del cotizador.
    """

    precio_rollo_filamento    = models.DecimalField(max_digits=12, decimal_places=2, default=80000,   verbose_name="Precio del rollo de filamento (COP)")
    peso_rollo_gramos         = models.DecimalField(max_digits=8,  decimal_places=2, default=1000,    verbose_name="Peso del rollo (g)")
    costo_electricidad_kwh    = models.DecimalField(max_digits=8,  decimal_places=2, default=850,     verbose_name="Costo electricidad (COP/kWh)")
    consumo_impresora_kw      = models.DecimalField(max_digits=6,  decimal_places=3, default=0.15,    verbose_name="Consumo impresora (kW)")
    valor_hora_trabajo        = models.DecimalField(max_digits=10, decimal_places=2, default=25000,   verbose_name="Valor hora de trabajo (COP/h)")
    margen_ganancia           = models.DecimalField(max_digits=5,  decimal_places=4, default=0.35,    verbose_name="Margen de ganancia (%)", validators=[MinValueValidator(0)])
    margen_fallos             = models.DecimalField(max_digits=5,  decimal_places=4, default=0.10,    verbose_name="Margen fallos (%)",      validators=[MinValueValidator(0)])
    costo_impresora           = models.DecimalField(max_digits=14, decimal_places=2, default=1500000, verbose_name="Costo de la impresora (COP)")
    vida_util_horas           = models.PositiveIntegerField(default=5000,                             verbose_name="Vida útil estimada (horas)")
    costo_mantenimiento_anual = models.DecimalField(max_digits=12, decimal_places=2, default=200000,  verbose_name="Costo mantenimiento anual (COP)")
    horas_totales_anio        = models.PositiveIntegerField(default=8760,                             verbose_name="Horas totales del año")
    costo_empaque             = models.DecimalField(max_digits=10, decimal_places=2, default=1500,    verbose_name="Costo de empaque (COP)")

    class Meta:
        verbose_name        = "Variables Fijas"
        verbose_name_plural = "Variables Fijas"

    def __str__(self):
        return "Configuración global"

    def save(self, *args, **kwargs):
        # Garantiza que solo exista un registro
        self.pk = 1
        super().save(*args, **kwargs)
