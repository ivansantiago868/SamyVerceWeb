"""
Management command: limpiar_datos

Elimina todos los datos operativos del sistema preservando la configuración
base (empresas, usuarios, variables fijas, tipos de material).

Uso:
    python manage.py limpiar_datos                    # muestra conteos, no borra
    python manage.py limpiar_datos --confirmar        # borra todo
    python manage.py limpiar_datos --empresa 1        # filtra por empresa
    python manage.py limpiar_datos --empresa 1 --confirmar
    python manage.py limpiar_datos --todo --confirmar # incluye clientes e impresoras
"""
from django.core.management.base import BaseCommand
from django.db import transaction, connection


SEPARADOR = "─" * 52


class Command(BaseCommand):
    help = "Limpia datos operativos (pedidos, ventas, tareas, gastos, inventario, insumos, clientes)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirmar",
            action="store_true",
            default=False,
            help="Ejecuta la eliminación. Sin este flag solo muestra un resumen.",
        )
        parser.add_argument(
            "--empresa",
            type=int,
            default=None,
            metavar="ID",
            help="Limpia únicamente los datos de la empresa con ese ID.",
        )
        parser.add_argument(
            "--todo",
            action="store_true",
            default=False,
            help="Incluye también Clientes e Impresoras (por defecto se conservan).",
        )

    # ------------------------------------------------------------------ #
    def handle(self, **options):
        from django.contrib.auth.models import User
        from apps.produccion.models import (
            Tarea, Venta, Pedido,
            PiezaImagen, InventarioPieza,
            Gasto, Insumo, Cliente, Impresora,
            Material, TipoMaterial, Empresa,
        )

        empresa_id = options["empresa"]
        confirmar  = options["confirmar"]
        borrar_todo = options["todo"]

        self.stdout.write(SEPARADOR)
        self.stdout.write("  LIMPIEZA DE BASE DE DATOS — SamyVerce")
        self.stdout.write(SEPARADOR)

        if empresa_id:
            self.stdout.write(f"  Empresa filtrada: ID={empresa_id}")
        else:
            self.stdout.write("  Alcance: TODAS las empresas")

        if not confirmar:
            self.stdout.write(self.style.WARNING(
                "  Modo SIMULACIÓN — pase --confirmar para borrar"
            ))
        self.stdout.write(SEPARADOR)

        # ── Definir pasos en orden que respeta FK constraints ──────────
        # Cada entrada: (etiqueta, queryset_fn)
        # queryset_fn recibe empresa_id y devuelve el queryset listo.

        def qs_tareas(eid):
            qs = Tarea.objects.all()
            return qs.filter(empresa_id=eid) if eid else qs

        def qs_ventas(eid):
            qs = Venta.objects.all()
            return qs.filter(empresa_id=eid) if eid else qs

        def qs_pedidos(eid):
            qs = Pedido.objects.all()
            return qs.filter(empresa_id=eid) if eid else qs

        def qs_pieza_imagen(_):
            # PiezaImagen no tiene empresa directa; se borra junto con InventarioPieza
            return PiezaImagen.objects.all()

        def qs_inventario(_):
            return InventarioPieza.objects.all()

        def qs_gastos(eid):
            qs = Gasto.objects.all()
            return qs.filter(empresa_id=eid) if eid else qs

        def qs_insumos(_):
            return Insumo.objects.all()

        def qs_materiales(eid):
            qs = Material.objects.all()
            return qs.filter(empresa_id=eid) if eid else qs

        def qs_tipos_material(eid):
            qs = TipoMaterial.objects.all()
            return qs.filter(empresa_id=eid) if eid else qs

        def qs_usuarios(eid):
            qs = User.objects.exclude(username="kivandy")
            if eid:
                qs = qs.filter(perfil__empresa_id=eid)
            return qs

        def qs_empresas(eid):
            qs = Empresa.objects.all()
            return qs.filter(id=eid) if eid else qs

        pasos = [
            ("Tareas",               qs_tareas),
            ("Ventas / Cotizaciones", qs_ventas),
            ("Pedidos",              qs_pedidos),
            ("Imágenes de pieza",    qs_pieza_imagen),
            ("Inventario de piezas", qs_inventario),
            ("Gastos",               qs_gastos),
            ("Insumos",              qs_insumos),
            ("Materiales",           qs_materiales),
            ("Tipos de material",    qs_tipos_material),
        ]

        if borrar_todo:
            def qs_clientes(_):
                return Cliente.objects.all()

            def qs_impresoras(_):
                return Impresora.objects.all()

            pasos += [
                ("Clientes",    qs_clientes),
                ("Impresoras",  qs_impresoras),
            ]

        pasos.append(("Usuarios (excl. kivandy)", qs_usuarios))
        pasos.append(("Empresas",                 qs_empresas))

        # ── Mostrar resumen ────────────────────────────────────────────
        total_registros = 0
        conteos = []
        for etiqueta, qs_fn in pasos:
            count = qs_fn(empresa_id).count()
            conteos.append((etiqueta, count))
            total_registros += count
            icono = "🟡" if count else "⬜"
            self.stdout.write(f"  {icono} {etiqueta:<28} {count:>6} registros")

        self.stdout.write(SEPARADOR)
        self.stdout.write(f"  {'TOTAL':<28} {total_registros:>6} registros")
        self.stdout.write(SEPARADOR)

        if total_registros == 0:
            self.stdout.write(self.style.SUCCESS("  Base de datos ya está limpia."))
            return

        if not confirmar:
            self.stdout.write("")
            self.stdout.write("  Para ejecutar la limpieza, corra:")
            cmd = "  python manage.py limpiar_datos --confirmar"
            if empresa_id:
                cmd += f" --empresa {empresa_id}"
            if borrar_todo:
                cmd += " --todo"
            self.stdout.write(self.style.WARNING(cmd))
            return

        # ── Confirmación adicional en consola ──────────────────────────
        self.stdout.write("")
        self.stdout.write(self.style.ERROR(
            f"  ⚠️  Se eliminarán {total_registros} registros. Esta acción NO se puede deshacer."
        ))
        respuesta = input("  ¿Confirmar? Escriba 'SI' para continuar: ").strip()
        if respuesta != "SI":
            self.stdout.write(self.style.WARNING("  Operación cancelada."))
            return

        # ── Ejecutar borrado en transacción ───────────────────────────
        self.stdout.write("")
        self.stdout.write("  Eliminando...")

        modelos_borrados = []

        with transaction.atomic():
            for etiqueta, qs_fn in pasos:
                qs = qs_fn(empresa_id)
                count = qs.count()
                if count:
                    if etiqueta.startswith("Ventas"):
                        for venta in qs:
                            venta.pedidos.clear()
                    modelo = qs.model
                    qs.delete()
                    modelos_borrados.append(modelo)
                    self.stdout.write(f"  ✅ {etiqueta:<28} eliminados: {count}")
                else:
                    self.stdout.write(f"  ⬜ {etiqueta:<28} sin registros")

        # ── Reiniciar secuencias (auto-increment) ─────────────────────
        # Usa MAX(id) actual para no colisionar con registros preservados
        self.stdout.write("")
        self.stdout.write("  Reiniciando secuencias...")
        with connection.cursor() as cursor:
            for modelo in modelos_borrados:
                tabla = modelo._meta.db_table
                try:
                    cursor.execute(
                        f"""
                        SELECT setval(
                            pg_get_serial_sequence(%s, 'id'),
                            COALESCE((SELECT MAX(id) FROM {tabla}), 0) + 1,
                            false
                        )
                        """,
                        [tabla],
                    )
                    cursor.execute(
                        f"SELECT COALESCE((SELECT MAX(id) FROM {tabla}), 0) + 1"
                    )
                    next_id = cursor.fetchone()[0]
                    self.stdout.write(f"  🔄 {tabla:<38} → próximo ID: {next_id}")
                except Exception:
                    pass  # tabla sin secuencia (ej: M2M intermedias)

        self.stdout.write(SEPARADOR)
        self.stdout.write(self.style.SUCCESS("  Limpieza completada exitosamente."))
        self.stdout.write(SEPARADOR)
