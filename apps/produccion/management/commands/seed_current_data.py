from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models.signals import post_save

from apps.produccion.signals import crear_perfil_usuario, crear_insumo_desde_gasto, crear_tarea_desde_pedido
from apps.produccion.models import (
    Empresa, PerfilUsuario, Cliente,
    Impresora, TipoMaterial, Material, Insumo, Gasto,
    VariablesFijas, InventarioPieza,
    Figura, FiguraPieza,
    Pedido, PedidoMaterial, Venta, Tarea,
)


EMPRESAS = [
    {'nombre': 'SamyVerce', 'nit': '', 'email': 'ivansantiago868@hotmail.com', 'telefono': '3046476072', 'direccion': 'cr 20#185-58', 'activa': True},
]

USERS = [
    {'username': 'kivandy', 'first_name': '', 'last_name': '', 'email': '', 'is_superuser': True, 'is_staff': True, 'password': 'Admin123!'},
    {'username': 'SamyVerce', 'first_name': '', 'last_name': '', 'email': 'ivansantiago868@hotmail.com', 'is_superuser': False, 'is_staff': True, 'password': 'Samy2024!'},
    {'username': 'maker', 'first_name': 'Samy Verce', 'last_name': 'maker', 'email': 'ivansantiago868@gmail.com', 'is_superuser': False, 'is_staff': True, 'password': 'Samy2024!'},
]

PERFILES = [
    {'username': 'SamyVerce', 'empresa_nombre': 'SamyVerce'},
    {'username': 'maker', 'empresa_nombre': 'SamyVerce'},
]

CLIENTES = [
    {'empresa_nombre': 'SamyVerce', 'nombre': 'Fusion Retro Gaming', 'tipo_documento': 'CE', 'documento': '2931364', 'email': '', 'telefono': '3125113818', 'direccion': 'Diagonal 42 A sur #81G-32 piso #2 Bogotá', 'notas': ''},
]

IMPRESORAS = [
    {'empresa_nombre': 'SamyVerce', 'nombre': 'BambuaLab X1C', 'tipo': 'Filamento', 'costo': Decimal('5000000.00'), 'vida_util_horas': 8000, 'costo_mantenimiento_anual': Decimal('300000.00'), 'consumo_promedio_kw': Decimal('0.130'), 'activa': True},
]

VARIABLES_FIJAS = [
    {'empresa_nombre': None, 'precio_rollo_filamento': Decimal('80000.00'), 'peso_rollo_gramos': Decimal('1000.00'), 'costo_electricidad_kwh': Decimal('850.00'), 'consumo_impresora_kw': Decimal('0.150'), 'valor_hora_trabajo': Decimal('25000.00'), 'margen_ganancia': Decimal('0.3500'), 'margen_fallos': Decimal('0.1000'), 'costo_impresora': Decimal('1500000.00'), 'vida_util_horas': 5000, 'costo_mantenimiento_anual': Decimal('200000.00'), 'horas_totales_anio': 8760, 'costo_empaque': Decimal('1500.00')},
    {'empresa_nombre': 'SamyVerce', 'precio_rollo_filamento': Decimal('80000.00'), 'peso_rollo_gramos': Decimal('1000.00'), 'costo_electricidad_kwh': Decimal('850.00'), 'consumo_impresora_kw': Decimal('0.150'), 'valor_hora_trabajo': Decimal('25000.00'), 'margen_ganancia': Decimal('0.3500'), 'margen_fallos': Decimal('0.1000'), 'costo_impresora': Decimal('1500000.00'), 'vida_util_horas': 5000, 'costo_mantenimiento_anual': Decimal('200000.00'), 'horas_totales_anio': 8760, 'costo_empaque': Decimal('1500.00')},
]

TIPOS_MATERIAL = [
    {'empresa_nombre': 'SamyVerce', 'nombre': 'PLA'},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'PETG'},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'ABS'},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'ASA'},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'TPU'},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'Resina'},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'Nylon'},
]

MATERIALES = [
    {'empresa_nombre': 'SamyVerce', 'nombre': 'PLA Estándar', 'tipo_nombre': 'PLA'},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'PLA+', 'tipo_nombre': 'PLA'},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'PLA Matte', 'tipo_nombre': 'PLA'},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'PLA Silk', 'tipo_nombre': 'PLA'},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'PLA Madera', 'tipo_nombre': 'PLA'},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'PETG Estándar', 'tipo_nombre': 'PETG'},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'PETG Carbon', 'tipo_nombre': 'PETG'},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'ABS Estándar', 'tipo_nombre': 'ABS'},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'ABS+', 'tipo_nombre': 'ABS'},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'ASA Estándar', 'tipo_nombre': 'ASA'},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'TPU 95A', 'tipo_nombre': 'TPU'},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'TPU 85A', 'tipo_nombre': 'TPU'},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'Resina Estándar', 'tipo_nombre': 'Resina'},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'Resina ABS-Like', 'tipo_nombre': 'Resina'},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'Resina Flexible', 'tipo_nombre': 'Resina'},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'Nylon PA12', 'tipo_nombre': 'Nylon'},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'Nylon PA6-GF', 'tipo_nombre': 'Nylon'},
]

INSUMOS = [
    {'empresa_nombre': 'SamyVerce', 'producto': '[CUUI-1] Filamento amarrillo', 'material_nombre': 'PLA Estándar', 'material_tipo': 'PLA', 'precio': Decimal('65000.00'), 'cantidad_inicial': Decimal('230.00'), 'cantidad_final': Decimal('80.00')},
    {'empresa_nombre': 'SamyVerce', 'producto': '[CUUI-2] Filamento Blanco', 'material_nombre': 'PLA Estándar', 'material_tipo': 'PLA', 'precio': Decimal('73810.00'), 'cantidad_inicial': Decimal('0.00'), 'cantidad_final': Decimal('520.00')},
]

GASTOS = [
    {'empresa_nombre': 'SamyVerce', 'articulo': 'Filamento amarrillo', 'material_nombre': 'PLA Estándar', 'material_tipo': 'PLA', 'peso': Decimal('1000.00'), 'costo': Decimal('65000.00'), 'fecha': date(2026, 4, 15)},
    {'empresa_nombre': 'SamyVerce', 'articulo': 'Filamento Blanco', 'material_nombre': 'PLA Estándar', 'material_tipo': 'PLA', 'peso': Decimal('1000.00'), 'costo': Decimal('73810.00'), 'fecha': date(2026, 4, 26)},
]

PIEZAS = [
    {'empresa_nombre': 'SamyVerce', 'nombre': 'Recuadro - Porta Juegos Nintendo Switch Diseño Retro GameBoy', 'peso_gramos': Decimal('70.00'), 'tiempo_impresion_horas': Decimal('4.00'), 'tiempo_postproceso_horas': Decimal('0.00'), 'costo_empaque': Decimal('0.00'), 'costo_material': Decimal('4550.00'), 'costo_energia': Decimal('510.00'), 'costo_tiempo': Decimal('0.00'), 'subtotal_produccion': Decimal('5060.00'), 'amortizacion_fallos': Decimal('506.00'), 'depreciacion_pieza': Decimal('2500.00'), 'mantenimiento_preventivo': Decimal('136.99'), 'costo_total_real': Decimal('8202.99'), 'precio_venta_sugerido': Decimal('13000.00'), 'url_referencia': None},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'Estuche - Porta Juegos Nintendo Switch Diseño Retro GameBoy', 'peso_gramos': Decimal('40.00'), 'tiempo_impresion_horas': Decimal('2.00'), 'tiempo_postproceso_horas': Decimal('0.00'), 'costo_empaque': Decimal('0.00'), 'costo_material': Decimal('2600.00'), 'costo_energia': Decimal('255.00'), 'costo_tiempo': Decimal('0.00'), 'subtotal_produccion': Decimal('2855.00'), 'amortizacion_fallos': Decimal('285.50'), 'depreciacion_pieza': Decimal('1250.00'), 'mantenimiento_preventivo': Decimal('68.49'), 'costo_total_real': Decimal('4458.99'), 'precio_venta_sugerido': Decimal('7000.00'), 'url_referencia': None},
    {'empresa_nombre': 'SamyVerce', 'nombre': 'Portada - Porta Juegos Nintendo Switch Diseño Retro GameBoy', 'peso_gramos': Decimal('20.00'), 'tiempo_impresion_horas': Decimal('6.00'), 'tiempo_postproceso_horas': Decimal('0.20'), 'costo_empaque': Decimal('0.00'), 'costo_material': Decimal('1300.00'), 'costo_energia': Decimal('765.00'), 'costo_tiempo': Decimal('5000.00'), 'subtotal_produccion': Decimal('7065.00'), 'amortizacion_fallos': Decimal('706.50'), 'depreciacion_pieza': Decimal('3750.00'), 'mantenimiento_preventivo': Decimal('205.48'), 'costo_total_real': Decimal('11726.98'), 'precio_venta_sugerido': Decimal('19000.00'), 'url_referencia': None},
]

FIGURAS = [
    {'empresa_nombre': 'SamyVerce', 'nombre': 'Porta Juegos Nintendo Switch Diseño Retro GameBoy', 'descripcion': '¿Extrañas los 90? Revive la época dorada del gaming mientras proteges tus títulos favoritos de Nintendo Switch. Este case premium con diseño icónico de GameBoy Classic es el accesorio definitivo para todo fan de la "Gran N".\r\n\r\nCapacidad: Guarda hasta 10 cartuchos de Switch y 2 tarjetas Micro SD.\r\n\r\nProtección Total: Interior de silicona suave de alta densidad que evita rayones y absorbe impactos.\r\n\r\nCierre Magnético: Seguro y fácil de abrir; tus juegos no se saldrán por accidente en el morral.\r\n\r\nPortátil: Diseño ultra compacto que cabe en cualquier bolsillo.\r\n\r\n¡El regalo perfecto para ti o para ese amigo fanático de lo retro!'},
]

FIGURA_PIEZAS = [
    {'figura_nombre': 'Porta Juegos Nintendo Switch Diseño Retro GameBoy', 'pieza_nombre': 'Estuche - Porta Juegos Nintendo Switch Diseño Retro GameBoy', 'insumo_producto': '[CUUI-2] Filamento Blanco', 'cantidad': 1},
    {'figura_nombre': 'Porta Juegos Nintendo Switch Diseño Retro GameBoy', 'pieza_nombre': 'Portada - Porta Juegos Nintendo Switch Diseño Retro GameBoy', 'insumo_producto': '[CUUI-1] Filamento amarrillo', 'cantidad': 1},
    {'figura_nombre': 'Porta Juegos Nintendo Switch Diseño Retro GameBoy', 'pieza_nombre': 'Recuadro - Porta Juegos Nintendo Switch Diseño Retro GameBoy', 'insumo_producto': '[CUUI-1] Filamento amarrillo', 'cantidad': 1},
]

PEDIDOS = [
    {'empresa_nombre': 'SamyVerce', 'numero_pedido': '100001', 'prioridad': 'Medio', 'cliente_nombre': 'Fusion Retro Gaming', 'figura_nombre': 'Porta Juegos Nintendo Switch Diseño Retro GameBoy', 'cantidad': 10, 'realizados': 10, 'precio_unidad': Decimal('39000.00'), 'fecha_entrega': date(2026, 4, 30), 'maquina_nombre': 'BambuaLab X1C', 'estado': 'Listo', 'descripcion': ''},
]

PEDIDO_MATERIALES = [
    {'pedido_numero': '100001', 'pedido_id': 1, 'pieza_nombre': 'Estuche - Porta Juegos Nintendo Switch Diseño Retro GameBoy', 'insumo_producto': '[CUUI-2] Filamento Blanco'},
    {'pedido_numero': '100001', 'pedido_id': 1, 'pieza_nombre': 'Portada - Porta Juegos Nintendo Switch Diseño Retro GameBoy', 'insumo_producto': '[CUUI-1] Filamento amarrillo'},
    {'pedido_numero': '100001', 'pedido_id': 1, 'pieza_nombre': 'Recuadro - Porta Juegos Nintendo Switch Diseño Retro GameBoy', 'insumo_producto': '[CUUI-1] Filamento amarrillo'},
]

VENTAS = [
    {'empresa_nombre': 'SamyVerce', 'fecha': date(2026, 4, 30), 'notas': '', 'pedido_numeros': ['100001'], 'pedido_ids': [1]},
]

TAREAS = [
    {'empresa_nombre': 'SamyVerce', 'prioridad': 'Medio', 'pedido_id': 1, 'cliente_nombre': 'Fusion Retro Gaming', 'cliente_texto': '', 'producto': 'Estuche - Porta Juegos Nintendo Switch Diseño Retro GameBoy', 'cantidad': 10, 'realizados': 10, 'precio_total': Decimal('70000.00'), 'fecha_entrega': date(2026, 4, 30), 'maquina_nombre': 'BambuaLab X1C', 'estado': 'Listo', 'descripcion': '[Porta Juegos Nintendo Switch Diseño Retro GameBoy]'},
    {'empresa_nombre': 'SamyVerce', 'prioridad': 'Medio', 'pedido_id': 1, 'cliente_nombre': 'Fusion Retro Gaming', 'cliente_texto': '', 'producto': 'Portada - Porta Juegos Nintendo Switch Diseño Retro GameBoy', 'cantidad': 10, 'realizados': 10, 'precio_total': Decimal('190000.00'), 'fecha_entrega': date(2026, 4, 30), 'maquina_nombre': 'BambuaLab X1C', 'estado': 'Listo', 'descripcion': '[Porta Juegos Nintendo Switch Diseño Retro GameBoy]'},
    {'empresa_nombre': 'SamyVerce', 'prioridad': 'Medio', 'pedido_id': 1, 'cliente_nombre': 'Fusion Retro Gaming', 'cliente_texto': '', 'producto': 'Recuadro - Porta Juegos Nintendo Switch Diseño Retro GameBoy', 'cantidad': 10, 'realizados': 10, 'precio_total': Decimal('130000.00'), 'fecha_entrega': date(2026, 4, 30), 'maquina_nombre': 'BambuaLab X1C', 'estado': 'Listo', 'descripcion': '[Porta Juegos Nintendo Switch Diseño Retro GameBoy]'},
]

class Command(BaseCommand):
    help = "Seed current data for SamyVerce after reset"

    def handle(self, *args, **options):
        post_save.disconnect(crear_perfil_usuario, sender=User)
        post_save.disconnect(crear_insumo_desde_gasto, sender=__import__("apps.produccion.models.gasto", fromlist=["Gasto"]).Gasto)
        post_save.disconnect(crear_tarea_desde_pedido, sender=Pedido)
        try:
            self._seed()
        finally:
            post_save.connect(crear_perfil_usuario, sender=User)
            post_save.connect(crear_insumo_desde_gasto, sender=__import__("apps.produccion.models.gasto", fromlist=["Gasto"]).Gasto)
            post_save.connect(crear_tarea_desde_pedido, sender=Pedido)

    def _seed(self):
        # Empresas
        empresas = {}
        for d in EMPRESAS:
            e, _ = Empresa.objects.get_or_create(nombre=d["nombre"], defaults={
                "nit": d["nit"], "email": d["email"], "telefono": d["telefono"],
                "direccion": d["direccion"], "activa": d["activa"],
            })
            empresas[e.nombre] = e

        # Usuarios
        users = {}
        for d in USERS:
            u, created = User.objects.get_or_create(username=d["username"], defaults={
                "first_name": d["first_name"], "last_name": d["last_name"],
                "email": d["email"], "is_superuser": d["is_superuser"], "is_staff": d["is_staff"],
            })
            if created:
                u.set_password(d["password"])
                u.save()
            users[u.username] = u

        for d in PERFILES:
            emp = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None
            PerfilUsuario.objects.get_or_create(usuario=users[d["username"]], defaults={"empresa": emp})

        # Clientes
        clientes = {}
        for d in CLIENTES:
            emp = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None
            c, _ = Cliente.objects.get_or_create(
                nombre=d["nombre"], empresa=emp,
                defaults={"tipo_documento": d["tipo_documento"], "documento": d["documento"],
                          "email": d["email"], "telefono": d["telefono"],
                          "direccion": d["direccion"], "notas": d["notas"]},
            )
            clientes[c.nombre] = c

        # Impresoras
        impresoras = {}
        for d in IMPRESORAS:
            emp = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None
            i, _ = Impresora.objects.get_or_create(
                nombre=d["nombre"], empresa=emp,
                defaults={"tipo": d["tipo"], "costo": d["costo"],
                          "vida_util_horas": d["vida_util_horas"],
                          "costo_mantenimiento_anual": d["costo_mantenimiento_anual"],
                          "consumo_promedio_kw": d["consumo_promedio_kw"],
                          "activa": d["activa"]},
            )
            impresoras[i.nombre] = i

        # Variables fijas
        for d in VARIABLES_FIJAS:
            emp = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None
            v, _ = VariablesFijas.objects.get_or_create(empresa=emp, defaults={
                k: d[k] for k in d if k != "empresa_nombre"
            })

        # Tipos de material
        tipos = {}
        for d in TIPOS_MATERIAL:
            emp = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None
            tm, _ = TipoMaterial.objects.get_or_create(nombre=d["nombre"], empresa=emp)
            tipos[tm.nombre] = tm

        # Materiales
        materiales = {}
        for d in MATERIALES:
            emp = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None
            tm = tipos[d["tipo_nombre"]]
            m, _ = Material.objects.get_or_create(nombre=d["nombre"], tipo=tm, defaults={"empresa": emp})
            materiales[(m.nombre, tm.nombre)] = m

        # Insumos
        insumos = {}
        for d in INSUMOS:
            emp = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None
            mat = materiales.get((d["material_nombre"], d["material_tipo"])) if d["material_nombre"] else None
            ins, _ = Insumo.objects.get_or_create(
                producto=d["producto"], empresa=emp,
                defaults={"material": mat, "precio": d["precio"],
                          "cantidad_inicial": d["cantidad_inicial"], "cantidad_final": d["cantidad_final"]},
            )
            insumos[ins.producto] = ins

        # Gastos
        for d in GASTOS:
            emp = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None
            mat = materiales.get((d["material_nombre"], d["material_tipo"])) if d["material_nombre"] else None
            Gasto.objects.get_or_create(
                articulo=d["articulo"], fecha=d["fecha"], empresa=emp,
                defaults={"material": mat, "peso": d["peso"], "costo": d["costo"]},
            )

        # Piezas
        piezas = {}
        for d in PIEZAS:
            emp = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None
            p, _ = InventarioPieza.objects.get_or_create(
                nombre=d["nombre"], empresa=emp,
                defaults={k: d[k] for k in d if k not in ("empresa_nombre", "nombre")},
            )
            piezas[p.nombre] = p

        # Figuras
        figuras = {}
        for d in FIGURAS:
            emp = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None
            f, _ = Figura.objects.get_or_create(
                nombre=d["nombre"], empresa=emp,
                defaults={"descripcion": d["descripcion"]},
            )
            figuras[f.nombre] = f

        # FiguraPiezas
        for d in FIGURA_PIEZAS:
            figura = figuras[d["figura_nombre"]]
            pieza  = piezas[d["pieza_nombre"]]
            ins    = insumos.get(d["insumo_producto"]) if d["insumo_producto"] else None
            FiguraPieza.objects.get_or_create(
                figura=figura, pieza=pieza,
                defaults={"insumo": ins, "cantidad": d["cantidad"]},
            )

        # Pedidos
        pedidos_map = {}
        for d in PEDIDOS:
            emp    = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None
            cliente = clientes.get(d["cliente_nombre"]) if d["cliente_nombre"] else None
            figura  = figuras.get(d["figura_nombre"]) if d["figura_nombre"] else None
            maquina = impresoras.get(d["maquina_nombre"]) if d["maquina_nombre"] else None
            p, _ = Pedido.objects.get_or_create(
                numero_pedido=d["numero_pedido"], empresa=emp,
                defaults={"prioridad": d["prioridad"], "cliente": cliente, "figura": figura,
                          "cantidad": d["cantidad"], "realizados": d["realizados"],
                          "precio_unidad": d["precio_unidad"], "fecha_entrega": d["fecha_entrega"],
                          "maquina": maquina, "estado": d["estado"], "descripcion": d["descripcion"]},
            )
            pedidos_map[p.id] = p
            if d["numero_pedido"]:
                pedidos_map[d["numero_pedido"]] = p

        # PedidoMateriales
        for d in PEDIDO_MATERIALES:
            pedido = pedidos_map.get(d["pedido_numero"]) or pedidos_map.get(d["pedido_id"])
            pieza  = piezas.get(d["pieza_nombre"])
            ins    = insumos.get(d["insumo_producto"]) if d["insumo_producto"] else None
            if pedido and pieza:
                PedidoMaterial.objects.get_or_create(
                    pedido=pedido, pieza=pieza, defaults={"material": ins},
                )

        # Ventas
        for d in VENTAS:
            emp = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None
            v, _ = Venta.objects.get_or_create(
                fecha=d["fecha"], empresa=emp,
                defaults={"notas": d["notas"]},
            )
            for num in d["pedido_numeros"]:
                p = pedidos_map.get(num)
                if p:
                    v.pedidos.add(p)
            for pid in d["pedido_ids"]:
                p = pedidos_map.get(pid)
                if p:
                    v.pedidos.add(p)

        # Tareas
        for d in TAREAS:
            emp     = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None
            cliente = clientes.get(d["cliente_nombre"]) if d["cliente_nombre"] else None
            maquina = impresoras.get(d["maquina_nombre"]) if d["maquina_nombre"] else None
            pedido  = pedidos_map.get(d["pedido_id"]) if d["pedido_id"] else None
            Tarea.objects.get_or_create(
                empresa=emp, producto=d["producto"], estado=d["estado"],
                defaults={"prioridad": d["prioridad"], "pedido": pedido, "cliente": cliente,
                          "cliente_texto": d["cliente_texto"], "cantidad": d["cantidad"],
                          "realizados": d["realizados"], "precio_total": d["precio_total"],
                          "fecha_entrega": d["fecha_entrega"], "maquina": maquina,
                          "descripcion": d["descripcion"]},
            )

        self.stdout.write(self.style.SUCCESS("✅ Seed completado exitosamente."))
