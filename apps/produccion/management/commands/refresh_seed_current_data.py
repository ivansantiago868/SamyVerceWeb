from pathlib import Path
from decimal import Decimal
from datetime import date, datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import User

from apps.produccion.models import (
    Empresa, PerfilUsuario, Cliente,
    Impresora, TipoMaterial, Material, Insumo, Gasto,
    VariablesFijas, InventarioPieza,
    Figura, FiguraPieza,
    Pedido, PedidoMaterial, Venta, Tarea,
)


def _py_quote(value):
    return repr(value)


def _py_date(value):
    if value is None:
        return 'None'
    return f"date({value.year}, {value.month}, {value.day})"


def _py_decimal(value):
    if value is None:
        return "Decimal('0.00')"
    return f"Decimal('{value}')"


def _format_value(value):
    if isinstance(value, Decimal):
        return _py_decimal(value)
    if isinstance(value, date):
        return _py_date(value)
    if isinstance(value, str):
        return _py_quote(value)
    if value is None:
        return 'None'
    return repr(value)


def _format_item(data):
    parts = []
    for key, value in data.items():
        parts.append(f"'{key}': {_format_value(value)}")
    return '{' + ', '.join(parts) + '}'


class Command(BaseCommand):
    help = 'Refresh seed_current_data.py based on current database state'

    def handle(self, *args, **options):
        commands_dir = Path(__file__).resolve().parent
        seed_file = commands_dir / 'seed_current_data.py'

        # --- Backup ---
        bk_dir = settings.BASE_DIR / 'BK'
        bk_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = bk_dir / f'db_backup_{timestamp}.json'
        self.stdout.write("Creando backup de la base de datos en carpeta BK...")
        try:
            call_command('dumpdata', exclude=['contenttypes', 'auth.Permission'], output=str(backup_file))
            self.stdout.write(self.style.SUCCESS(f"✅ Backup creado: {backup_file.name}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error al crear backup: {e}"))

        # --- Leer datos ---
        empresas        = list(Empresa.objects.order_by('id'))
        users           = list(User.objects.order_by('id'))
        perfiles        = list(PerfilUsuario.objects.select_related('usuario', 'empresa').order_by('id'))
        clientes        = list(Cliente.objects.select_related('empresa').order_by('id'))
        impresoras      = list(Impresora.objects.select_related('empresa').order_by('id'))
        variables       = list(VariablesFijas.objects.select_related('empresa').order_by('id'))
        tipos_material  = list(TipoMaterial.objects.select_related('empresa').order_by('id'))
        materiales      = list(Material.objects.select_related('empresa', 'tipo').order_by('id'))
        insumos         = list(Insumo.objects.select_related('empresa', 'material').order_by('id'))
        gastos          = list(Gasto.objects.select_related('empresa', 'material').order_by('cuui'))
        piezas          = list(InventarioPieza.objects.select_related('empresa').order_by('id'))
        figuras         = list(Figura.objects.select_related('empresa').order_by('id'))
        figura_piezas   = list(FiguraPieza.objects.select_related('figura', 'pieza', 'insumo').order_by('id'))
        pedidos         = list(Pedido.objects.select_related('empresa', 'cliente', 'figura', 'maquina').order_by('id'))
        pedido_mats     = list(PedidoMaterial.objects.select_related('pedido', 'pieza', 'material').order_by('id'))
        ventas          = list(Venta.objects.prefetch_related('pedidos').select_related('empresa').order_by('id'))
        tareas          = list(Tarea.objects.select_related('empresa', 'pedido', 'cliente', 'maquina').order_by('id'))

        # --- Serializar ---
        empresa_items = []
        for e in empresas:
            empresa_items.append({
                'nombre':   e.nombre,
                'nit':      e.nit,
                'email':    e.email,
                'telefono': e.telefono,
                'direccion': e.direccion,
                'activa':   e.activa,
            })

        user_items = []
        for u in users:
            user_items.append({
                'username':   u.username,
                'first_name': u.first_name,
                'last_name':  u.last_name,
                'email':      u.email,
                'is_superuser': u.is_superuser,
                'is_staff':   u.is_staff,
                'password':   'Admin123!' if u.is_superuser else 'Samy2024!',
            })

        perfil_items = []
        for p in perfiles:
            perfil_items.append({
                'username':      p.usuario.username,
                'empresa_nombre': p.empresa.nombre if p.empresa else None,
            })

        cliente_items = []
        for c in clientes:
            cliente_items.append({
                'empresa_nombre': c.empresa.nombre if c.empresa else None,
                'nombre':         c.nombre,
                'tipo_documento': c.tipo_documento,
                'documento':      c.documento,
                'email':          c.email,
                'telefono':       c.telefono,
                'direccion':      c.direccion,
                'notas':          c.notas,
            })

        impresora_items = []
        for i in impresoras:
            impresora_items.append({
                'empresa_nombre':           i.empresa.nombre if i.empresa else None,
                'nombre':                   i.nombre,
                'tipo':                     i.tipo,
                'costo':                    i.costo,
                'vida_util_horas':          i.vida_util_horas,
                'costo_mantenimiento_anual': i.costo_mantenimiento_anual,
                'consumo_promedio_kw':      i.consumo_promedio_kw,
                'activa':                   i.activa,
            })

        variables_items = []
        for v in variables:
            variables_items.append({
                'empresa_nombre':           v.empresa.nombre if v.empresa else None,
                'precio_rollo_filamento':   v.precio_rollo_filamento,
                'peso_rollo_gramos':        v.peso_rollo_gramos,
                'costo_electricidad_kwh':   v.costo_electricidad_kwh,
                'consumo_impresora_kw':     v.consumo_impresora_kw,
                'valor_hora_trabajo':       v.valor_hora_trabajo,
                'margen_ganancia':          v.margen_ganancia,
                'margen_fallos':            v.margen_fallos,
                'costo_impresora':          v.costo_impresora,
                'vida_util_horas':          v.vida_util_horas,
                'costo_mantenimiento_anual': v.costo_mantenimiento_anual,
                'horas_totales_anio':       v.horas_totales_anio,
                'costo_empaque':            v.costo_empaque,
            })

        tipo_material_items = []
        for tm in tipos_material:
            tipo_material_items.append({
                'empresa_nombre': tm.empresa.nombre if tm.empresa else None,
                'nombre':         tm.nombre,
            })

        material_items = []
        for m in materiales:
            material_items.append({
                'empresa_nombre':    m.empresa.nombre if m.empresa else None,
                'nombre':            m.nombre,
                'tipo_nombre':       m.tipo.nombre,
            })

        insumo_items = []
        for ins in insumos:
            insumo_items.append({
                'empresa_nombre':  ins.empresa.nombre if ins.empresa else None,
                'producto':        ins.producto,
                'material_nombre': ins.material.nombre if ins.material else None,
                'material_tipo':   ins.material.tipo.nombre if ins.material else None,
                'precio':          ins.precio,
                'cantidad_inicial': ins.cantidad_inicial,
                'cantidad_final':  ins.cantidad_final,
            })

        gasto_items = []
        for g in gastos:
            gasto_items.append({
                'empresa_nombre':  g.empresa.nombre if g.empresa else None,
                'articulo':        g.articulo,
                'material_nombre': g.material.nombre if g.material else None,
                'material_tipo':   g.material.tipo.nombre if g.material else None,
                'peso':            g.peso,
                'costo':           g.costo,
                'fecha':           g.fecha,
            })

        pieza_items = []
        for p in piezas:
            pieza_items.append({
                'empresa_nombre':          p.empresa.nombre if p.empresa else None,
                'nombre':                  p.nombre,
                'peso_gramos':             p.peso_gramos,
                'tiempo_impresion_horas':  p.tiempo_impresion_horas,
                'tiempo_postproceso_horas': p.tiempo_postproceso_horas,
                'costo_empaque':           p.costo_empaque,
                'costo_material':          p.costo_material,
                'costo_energia':           p.costo_energia,
                'costo_tiempo':            p.costo_tiempo,
                'subtotal_produccion':     p.subtotal_produccion,
                'amortizacion_fallos':     p.amortizacion_fallos,
                'depreciacion_pieza':      p.depreciacion_pieza,
                'mantenimiento_preventivo': p.mantenimiento_preventivo,
                'costo_total_real':        p.costo_total_real,
                'precio_venta_sugerido':   p.precio_venta_sugerido,
                'url_referencia':          p.url_referencia,
            })

        figura_items = []
        for f in figuras:
            figura_items.append({
                'empresa_nombre': f.empresa.nombre if f.empresa else None,
                'nombre':         f.nombre,
                'descripcion':    f.descripcion,
            })

        figura_pieza_items = []
        for fp in figura_piezas:
            figura_pieza_items.append({
                'figura_nombre': fp.figura.nombre,
                'pieza_nombre':  fp.pieza.nombre,
                'insumo_producto': fp.insumo.producto if fp.insumo else None,
                'cantidad':      fp.cantidad,
            })

        pedido_items = []
        for p in pedidos:
            pedido_items.append({
                'empresa_nombre':  p.empresa.nombre if p.empresa else None,
                'numero_pedido':   p.numero_pedido,
                'prioridad':       p.prioridad,
                'cliente_nombre':  p.cliente.nombre if p.cliente else None,
                'figura_nombre':   p.figura.nombre if p.figura else None,
                'cantidad':        p.cantidad,
                'realizados':      p.realizados,
                'precio_unidad':   p.precio_unidad,
                'fecha_entrega':   p.fecha_entrega,
                'maquina_nombre':  p.maquina.nombre if p.maquina else None,
                'estado':          p.estado,
                'descripcion':     p.descripcion,
            })

        pedido_mat_items = []
        for pm in pedido_mats:
            pedido_mat_items.append({
                'pedido_numero':   pm.pedido.numero_pedido,
                'pedido_id':       pm.pedido.id,
                'pieza_nombre':    pm.pieza.nombre,
                'insumo_producto': pm.material.producto if pm.material else None,
            })

        venta_items = []
        for v in ventas:
            venta_items.append({
                'empresa_nombre':  v.empresa.nombre if v.empresa else None,
                'fecha':           v.fecha,
                'notas':           v.notas,
                'pedido_numeros':  [p.numero_pedido for p in v.pedidos.all()],
                'pedido_ids':      [p.id for p in v.pedidos.all()],
            })

        tarea_items = []
        for t in tareas:
            tarea_items.append({
                'empresa_nombre':  t.empresa.nombre if t.empresa else None,
                'prioridad':       t.prioridad,
                'pedido_id':       t.pedido.id if t.pedido else None,
                'cliente_nombre':  t.cliente.nombre if t.cliente else None,
                'cliente_texto':   t.cliente_texto,
                'producto':        t.producto,
                'cantidad':        t.cantidad,
                'realizados':      t.realizados,
                'precio_total':    t.precio_total,
                'fecha_entrega':   t.fecha_entrega,
                'maquina_nombre':  t.maquina.nombre if t.maquina else None,
                'estado':          t.estado,
                'descripcion':     t.descripcion,
            })

        # --- Generar archivo ---
        lines = [
            'from datetime import date',
            'from decimal import Decimal',
            '',
            'from django.contrib.auth.models import User',
            'from django.core.management.base import BaseCommand',
            'from django.db.models.signals import post_save',
            '',
            'from apps.produccion.signals import crear_perfil_usuario, crear_insumo_desde_gasto, crear_tarea_desde_pedido',
            'from apps.produccion.models import (',
            '    Empresa, PerfilUsuario, Cliente,',
            '    Impresora, TipoMaterial, Material, Insumo, Gasto,',
            '    VariablesFijas, InventarioPieza,',
            '    Figura, FiguraPieza,',
            '    Pedido, PedidoMaterial, Venta, Tarea,',
            ')',
            '',
            '',
        ]

        def write_list(name, items):
            lines.append(f'{name} = [')
            for item in items:
                lines.append('    ' + _format_item(item) + ',')
            lines.append(']')
            lines.append('')

        write_list('EMPRESAS', empresa_items)
        write_list('USERS', user_items)
        write_list('PERFILES', perfil_items)
        write_list('CLIENTES', cliente_items)
        write_list('IMPRESORAS', impresora_items)
        write_list('VARIABLES_FIJAS', variables_items)
        write_list('TIPOS_MATERIAL', tipo_material_items)
        write_list('MATERIALES', material_items)
        write_list('INSUMOS', insumo_items)
        write_list('GASTOS', gasto_items)
        write_list('PIEZAS', pieza_items)
        write_list('FIGURAS', figura_items)
        write_list('FIGURA_PIEZAS', figura_pieza_items)
        write_list('PEDIDOS', pedido_items)
        write_list('PEDIDO_MATERIALES', pedido_mat_items)
        write_list('VENTAS', venta_items)
        write_list('TAREAS', tarea_items)

        lines.extend([
            'class Command(BaseCommand):',
            '    help = "Seed current data for SamyVerce after reset"',
            '',
            '    def handle(self, *args, **options):',
            '        post_save.disconnect(crear_perfil_usuario, sender=User)',
            '        post_save.disconnect(crear_insumo_desde_gasto, sender=__import__("apps.produccion.models.gasto", fromlist=["Gasto"]).Gasto)',
            '        post_save.disconnect(crear_tarea_desde_pedido, sender=Pedido)',
            '        try:',
            '            self._seed()',
            '        finally:',
            '            post_save.connect(crear_perfil_usuario, sender=User)',
            '            post_save.connect(crear_insumo_desde_gasto, sender=__import__("apps.produccion.models.gasto", fromlist=["Gasto"]).Gasto)',
            '            post_save.connect(crear_tarea_desde_pedido, sender=Pedido)',
            '',
            '    def _seed(self):',
            '        # Empresas',
            '        empresas = {}',
            '        for d in EMPRESAS:',
            '            e, _ = Empresa.objects.get_or_create(nombre=d["nombre"], defaults={',
            '                "nit": d["nit"], "email": d["email"], "telefono": d["telefono"],',
            '                "direccion": d["direccion"], "activa": d["activa"],',
            '            })',
            '            empresas[e.nombre] = e',
            '',
            '        # Usuarios',
            '        users = {}',
            '        for d in USERS:',
            '            u, created = User.objects.get_or_create(username=d["username"], defaults={',
            '                "first_name": d["first_name"], "last_name": d["last_name"],',
            '                "email": d["email"], "is_superuser": d["is_superuser"], "is_staff": d["is_staff"],',
            '            })',
            '            if created:',
            '                u.set_password(d["password"])',
            '                u.save()',
            '            users[u.username] = u',
            '',
            '        for d in PERFILES:',
            '            emp = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None',
            '            PerfilUsuario.objects.get_or_create(usuario=users[d["username"]], defaults={"empresa": emp})',
            '',
            '        # Clientes',
            '        clientes = {}',
            '        for d in CLIENTES:',
            '            emp = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None',
            '            c, _ = Cliente.objects.get_or_create(',
            '                nombre=d["nombre"], empresa=emp,',
            '                defaults={"tipo_documento": d["tipo_documento"], "documento": d["documento"],',
            '                          "email": d["email"], "telefono": d["telefono"],',
            '                          "direccion": d["direccion"], "notas": d["notas"]},',
            '            )',
            '            clientes[c.nombre] = c',
            '',
            '        # Impresoras',
            '        impresoras = {}',
            '        for d in IMPRESORAS:',
            '            emp = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None',
            '            i, _ = Impresora.objects.get_or_create(',
            '                nombre=d["nombre"], empresa=emp,',
            '                defaults={"tipo": d["tipo"], "costo": d["costo"],',
            '                          "vida_util_horas": d["vida_util_horas"],',
            '                          "costo_mantenimiento_anual": d["costo_mantenimiento_anual"],',
            '                          "consumo_promedio_kw": d["consumo_promedio_kw"],',
            '                          "activa": d["activa"]},',
            '            )',
            '            impresoras[i.nombre] = i',
            '',
            '        # Variables fijas',
            '        for d in VARIABLES_FIJAS:',
            '            emp = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None',
            '            v, _ = VariablesFijas.objects.get_or_create(empresa=emp, defaults={',
            '                k: d[k] for k in d if k != "empresa_nombre"',
            '            })',
            '',
            '        # Tipos de material',
            '        tipos = {}',
            '        for d in TIPOS_MATERIAL:',
            '            emp = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None',
            '            tm, _ = TipoMaterial.objects.get_or_create(nombre=d["nombre"], empresa=emp)',
            '            tipos[tm.nombre] = tm',
            '',
            '        # Materiales',
            '        materiales = {}',
            '        for d in MATERIALES:',
            '            emp = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None',
            '            tm = tipos[d["tipo_nombre"]]',
            '            m, _ = Material.objects.get_or_create(nombre=d["nombre"], tipo=tm, defaults={"empresa": emp})',
            '            materiales[(m.nombre, tm.nombre)] = m',
            '',
            '        # Insumos',
            '        insumos = {}',
            '        for d in INSUMOS:',
            '            emp = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None',
            '            mat = materiales.get((d["material_nombre"], d["material_tipo"])) if d["material_nombre"] else None',
            '            ins, _ = Insumo.objects.get_or_create(',
            '                producto=d["producto"], empresa=emp,',
            '                defaults={"material": mat, "precio": d["precio"],',
            '                          "cantidad_inicial": d["cantidad_inicial"], "cantidad_final": d["cantidad_final"]},',
            '            )',
            '            insumos[ins.producto] = ins',
            '',
            '        # Gastos',
            '        for d in GASTOS:',
            '            emp = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None',
            '            mat = materiales.get((d["material_nombre"], d["material_tipo"])) if d["material_nombre"] else None',
            '            Gasto.objects.get_or_create(',
            '                articulo=d["articulo"], fecha=d["fecha"], empresa=emp,',
            '                defaults={"material": mat, "peso": d["peso"], "costo": d["costo"]},',
            '            )',
            '',
            '        # Piezas',
            '        piezas = {}',
            '        for d in PIEZAS:',
            '            emp = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None',
            '            p, _ = InventarioPieza.objects.get_or_create(',
            '                nombre=d["nombre"], empresa=emp,',
            '                defaults={k: d[k] for k in d if k not in ("empresa_nombre", "nombre")},',
            '            )',
            '            piezas[p.nombre] = p',
            '',
            '        # Figuras',
            '        figuras = {}',
            '        for d in FIGURAS:',
            '            emp = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None',
            '            f, _ = Figura.objects.get_or_create(',
            '                nombre=d["nombre"], empresa=emp,',
            '                defaults={"descripcion": d["descripcion"]},',
            '            )',
            '            figuras[f.nombre] = f',
            '',
            '        # FiguraPiezas',
            '        for d in FIGURA_PIEZAS:',
            '            figura = figuras[d["figura_nombre"]]',
            '            pieza  = piezas[d["pieza_nombre"]]',
            '            ins    = insumos.get(d["insumo_producto"]) if d["insumo_producto"] else None',
            '            FiguraPieza.objects.get_or_create(',
            '                figura=figura, pieza=pieza,',
            '                defaults={"insumo": ins, "cantidad": d["cantidad"]},',
            '            )',
            '',
            '        # Pedidos',
            '        pedidos_map = {}',
            '        for d in PEDIDOS:',
            '            emp    = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None',
            '            cliente = clientes.get(d["cliente_nombre"]) if d["cliente_nombre"] else None',
            '            figura  = figuras.get(d["figura_nombre"]) if d["figura_nombre"] else None',
            '            maquina = impresoras.get(d["maquina_nombre"]) if d["maquina_nombre"] else None',
            '            p, _ = Pedido.objects.get_or_create(',
            '                numero_pedido=d["numero_pedido"], empresa=emp,',
            '                defaults={"prioridad": d["prioridad"], "cliente": cliente, "figura": figura,',
            '                          "cantidad": d["cantidad"], "realizados": d["realizados"],',
            '                          "precio_unidad": d["precio_unidad"], "fecha_entrega": d["fecha_entrega"],',
            '                          "maquina": maquina, "estado": d["estado"], "descripcion": d["descripcion"]},',
            '            )',
            '            pedidos_map[p.id] = p',
            '            if d["numero_pedido"]:',
            '                pedidos_map[d["numero_pedido"]] = p',
            '',
            '        # PedidoMateriales',
            '        for d in PEDIDO_MATERIALES:',
            '            pedido = pedidos_map.get(d["pedido_numero"]) or pedidos_map.get(d["pedido_id"])',
            '            pieza  = piezas.get(d["pieza_nombre"])',
            '            ins    = insumos.get(d["insumo_producto"]) if d["insumo_producto"] else None',
            '            if pedido and pieza:',
            '                PedidoMaterial.objects.get_or_create(',
            '                    pedido=pedido, pieza=pieza, defaults={"material": ins},',
            '                )',
            '',
            '        # Ventas',
            '        for d in VENTAS:',
            '            emp = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None',
            '            v, _ = Venta.objects.get_or_create(',
            '                fecha=d["fecha"], empresa=emp,',
            '                defaults={"notas": d["notas"]},',
            '            )',
            '            for num in d["pedido_numeros"]:',
            '                p = pedidos_map.get(num)',
            '                if p:',
            '                    v.pedidos.add(p)',
            '            for pid in d["pedido_ids"]:',
            '                p = pedidos_map.get(pid)',
            '                if p:',
            '                    v.pedidos.add(p)',
            '',
            '        # Tareas',
            '        for d in TAREAS:',
            '            emp     = empresas.get(d["empresa_nombre"]) if d["empresa_nombre"] else None',
            '            cliente = clientes.get(d["cliente_nombre"]) if d["cliente_nombre"] else None',
            '            maquina = impresoras.get(d["maquina_nombre"]) if d["maquina_nombre"] else None',
            '            pedido  = pedidos_map.get(d["pedido_id"]) if d["pedido_id"] else None',
            '            Tarea.objects.get_or_create(',
            '                empresa=emp, producto=d["producto"], estado=d["estado"],',
            '                defaults={"prioridad": d["prioridad"], "pedido": pedido, "cliente": cliente,',
            '                          "cliente_texto": d["cliente_texto"], "cantidad": d["cantidad"],',
            '                          "realizados": d["realizados"], "precio_total": d["precio_total"],',
            '                          "fecha_entrega": d["fecha_entrega"], "maquina": maquina,',
            '                          "descripcion": d["descripcion"]},',
            '            )',
            '',
            '        self.stdout.write(self.style.SUCCESS("✅ Seed completado exitosamente."))',
        ])

        seed_file.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        self.stdout.write(self.style.SUCCESS(f'✅ Archivo actualizado: {seed_file}'))
