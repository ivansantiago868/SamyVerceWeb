import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        # ── Tablas sin dependencias ──────────────────────────────────────
        migrations.CreateModel(
            name="Cliente",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=255, verbose_name="Nombre / Razón social")),
                ("tipo_documento", models.CharField(
                    blank=True,
                    choices=[
                        ("CC",  "Cédula de Ciudadanía"),
                        ("PPT", "Permiso de Protección Temporal"),
                        ("NIT", "NIT"),
                        ("CE",  "Cédula Extranjería"),
                        ("PAS", "Pasaporte"),
                    ],
                    max_length=5,
                )),
                ("documento", models.CharField(blank=True, max_length=30, verbose_name="Número de documento")),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("telefono", models.CharField(blank=True, max_length=20, verbose_name="Teléfono")),
                ("direccion", models.TextField(blank=True, verbose_name="Dirección")),
                ("notas", models.TextField(blank=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Cliente",
                "verbose_name_plural": "Clientes",
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="Impresora",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=100)),
                ("tipo", models.CharField(
                    choices=[
                        ("Filamento", "Filamento (FDM)"),
                        ("Resina",    "Resina (SLA/MSLA)"),
                        ("Lacer",     "Láser"),
                    ],
                    default="Filamento",
                    max_length=20,
                )),
                ("costo", models.DecimalField(decimal_places=2, max_digits=14, verbose_name="Costo (COP)")),
                ("vida_util_horas", models.PositiveIntegerField(verbose_name="Vida útil estimada (horas)")),
                ("costo_mantenimiento_anual", models.DecimalField(decimal_places=2, max_digits=12, verbose_name="Costo mantenimiento anual (COP)")),
                ("activa", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Impresora",
                "verbose_name_plural": "Impresoras",
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="Insumo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("producto", models.CharField(max_length=255, verbose_name="Producto")),
                ("cantidad_inicial", models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name="Cantidad inicial (g)")),
                ("cantidad_final", models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name="Cantidad final (g)")),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Insumo",
                "verbose_name_plural": "Insumos",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="Gasto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cuui", models.PositiveIntegerField(unique=True, verbose_name="CUUI")),
                ("articulo", models.CharField(max_length=255, verbose_name="Artículo")),
                ("peso", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Peso (g)")),
                ("costo", models.DecimalField(decimal_places=2, max_digits=14, verbose_name="Costo (COP)")),
                ("fecha", models.DateField(verbose_name="Fecha de compra")),
            ],
            options={
                "verbose_name": "Gasto",
                "verbose_name_plural": "Gastos",
                "ordering": ["-fecha", "cuui"],
            },
        ),
        migrations.CreateModel(
            name="VariablesFijas",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("precio_rollo_filamento", models.DecimalField(decimal_places=2, default=80000, max_digits=12, verbose_name="Precio del rollo de filamento (COP)")),
                ("peso_rollo_gramos", models.DecimalField(decimal_places=2, default=1000, max_digits=8, verbose_name="Peso del rollo (g)")),
                ("costo_electricidad_kwh", models.DecimalField(decimal_places=2, default=850, max_digits=8, verbose_name="Costo electricidad (COP/kWh)")),
                ("consumo_impresora_kw", models.DecimalField(decimal_places=3, default=0.15, max_digits=6, verbose_name="Consumo impresora (kW)")),
                ("valor_hora_trabajo", models.DecimalField(decimal_places=2, default=25000, max_digits=10, verbose_name="Valor hora de trabajo (COP/h)")),
                ("margen_ganancia", models.DecimalField(
                    decimal_places=4, default=0.35, max_digits=5,
                    validators=[django.core.validators.MinValueValidator(0)],
                    verbose_name="Margen de ganancia (%)",
                )),
                ("margen_fallos", models.DecimalField(
                    decimal_places=4, default=0.10, max_digits=5,
                    validators=[django.core.validators.MinValueValidator(0)],
                    verbose_name="Margen fallos (%)",
                )),
                ("costo_impresora", models.DecimalField(decimal_places=2, default=1500000, max_digits=14, verbose_name="Costo de la impresora (COP)")),
                ("vida_util_horas", models.PositiveIntegerField(default=5000, verbose_name="Vida útil estimada (horas)")),
                ("costo_mantenimiento_anual", models.DecimalField(decimal_places=2, default=200000, max_digits=12, verbose_name="Costo mantenimiento anual (COP)")),
                ("horas_totales_anio", models.PositiveIntegerField(default=8760, verbose_name="Horas totales del año")),
                ("costo_empaque", models.DecimalField(decimal_places=2, default=1500, max_digits=10, verbose_name="Costo de empaque (COP)")),
            ],
            options={
                "verbose_name": "Variables Fijas",
                "verbose_name_plural": "Variables Fijas",
            },
        ),
        migrations.CreateModel(
            name="InventarioPieza",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=255, verbose_name="Nombre de la pieza")),
                ("peso_gramos", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Peso estimado (g)")),
                ("tiempo_impresion_horas", models.DecimalField(decimal_places=2, max_digits=8, verbose_name="Tiempo de impresión (h)")),
                ("tiempo_postproceso_horas", models.DecimalField(decimal_places=2, default=0, max_digits=8, verbose_name="Tiempo post-procesado (h)")),
                ("costo_empaque", models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name="Costo empaque (COP)")),
                ("costo_material", models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Costo material (COP)")),
                ("costo_energia", models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Costo energía (COP)")),
                ("costo_tiempo", models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Costo tiempo (COP)")),
                ("subtotal_produccion", models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Subtotal producción (COP)")),
                ("amortizacion_fallos", models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Amortización fallos (COP)")),
                ("depreciacion_pieza", models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Depreciación por pieza (COP)")),
                ("mantenimiento_preventivo", models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Mantenimiento preventivo (COP)")),
                ("costo_total_real", models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Costo total real (COP)")),
                ("precio_venta_sugerido", models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Precio venta sugerido (COP)")),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Pieza (Inventario)",
                "verbose_name_plural": "Inventario de Piezas",
                "ordering": ["nombre"],
            },
        ),
        # ── Tablas con FK ────────────────────────────────────────────────
        migrations.CreateModel(
            name="Pedido",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("prioridad", models.CharField(
                    choices=[("Alto", "Alto"), ("Medio", "Medio"), ("Bajo", "Bajo")],
                    default="Medio",
                    max_length=10,
                )),
                ("cliente", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    to="produccion.cliente",
                )),
                ("cliente_texto", models.CharField(blank=True, max_length=255, verbose_name="Cliente (texto libre)")),
                ("producto", models.CharField(max_length=255)),
                ("material", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    to="produccion.insumo",
                    verbose_name="Material",
                )),
                ("cantidad", models.PositiveIntegerField(default=0)),
                ("realizados", models.PositiveIntegerField(default=0)),
                ("gr_pieza", models.DecimalField(decimal_places=2, default=0, max_digits=8, verbose_name="Gramos por pieza")),
                ("precio_unidad", models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Precio unitario (COP)")),
                ("fecha_entrega", models.DateField(blank=True, null=True)),
                ("maquina", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to="produccion.impresora",
                    verbose_name="Máquina",
                )),
                ("estado", models.CharField(
                    choices=[
                        ("Pendiente",      "Pendiente"),
                        ("En cola",        "En cola"),
                        ("Imprimiendo",    "Imprimiendo"),
                        ("Post-procesado", "Post-procesado"),
                        ("Listo",          "Listo"),
                        ("Entregado",      "Entregado"),
                        ("Cancelado",      "Cancelado"),
                    ],
                    default="Pendiente",
                    max_length=20,
                )),
                ("descripcion", models.TextField(blank=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Pedido",
                "verbose_name_plural": "Pedidos",
                "ordering": ["-creado_en"],
            },
        ),
        migrations.CreateModel(
            name="Venta",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fecha", models.DateField(verbose_name="Fecha de venta")),
                ("articulo", models.CharField(max_length=255, verbose_name="Artículo vendido")),
                ("cantidad", models.PositiveIntegerField(default=1)),
                ("pedido", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="ventas",
                    to="produccion.pedido",
                )),
                ("cliente", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to="produccion.cliente",
                )),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Venta",
                "verbose_name_plural": "Ventas",
                "ordering": ["-fecha"],
            },
        ),
        migrations.CreateModel(
            name="Tarea",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("prioridad", models.CharField(
                    choices=[("Alto", "Alto"), ("Medio", "Medio"), ("Bajo", "Bajo")],
                    default="Medio",
                    max_length=10,
                )),
                ("pedido", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="tareas",
                    to="produccion.pedido",
                )),
                ("cliente_texto", models.CharField(blank=True, max_length=255, verbose_name="Cliente")),
                ("producto", models.CharField(max_length=255)),
                ("cantidad", models.PositiveIntegerField(default=0)),
                ("realizados", models.PositiveIntegerField(default=0)),
                ("precio_total", models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name="Precio total (COP)")),
                ("fecha_entrega", models.DateField(blank=True, null=True)),
                ("maquina", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to="produccion.impresora",
                )),
                ("estado", models.CharField(
                    choices=[
                        ("Pendiente",      "Pendiente"),
                        ("En cola",        "En cola"),
                        ("Imprimiendo",    "Imprimiendo"),
                        ("Post-procesado", "Post-procesado"),
                        ("Listo",          "Listo"),
                        ("Entregado",      "Entregado"),
                        ("Cancelado",      "Cancelado"),
                    ],
                    default="Pendiente",
                    max_length=20,
                )),
                ("descripcion", models.TextField(blank=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Tarea",
                "verbose_name_plural": "Tareas",
                "ordering": ["fecha_entrega", "prioridad"],
            },
        ),
    ]