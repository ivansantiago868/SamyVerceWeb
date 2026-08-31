"""
views/produccion_view.py
ViewSets para: VariablesFijas, InventarioPieza, Pedido, Venta, Tarea.
Responsabilidad: solo HTTP (rutas, status codes, respuestas).
Lógica de negocio → controllers/
"""
import io
import zipfile

from django.http import HttpResponse
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_filters.rest_framework import DjangoFilterBackend

from apps.produccion.models import VariablesFijas, InventarioPieza, Pedido, Venta, Tarea, Figura, FiguraPieza, Cliente
from apps.produccion.serializers import (
    VariablesFijasSerializer, InventarioPiezaSerializer,
    PedidoSerializer, VentaSerializer, TareaSerializer,
    FiguraSerializer, FiguraPiezaSerializer, FiguraPublicaSerializer,
)
from apps.produccion.services import PedidoService, VentaService, TareaService
from apps.produccion.controllers.variables_fijas_controller import VariablesFijasController


# ── Mixin multi-tenant para ViewSets ─────────────────────────
class EmpresaViewSetMixin:
    """
    Filtra queryset y asigna empresa según el usuario autenticado.

    Flujo de empresa:
      request.user → auth_user
        → PerfilUsuario.usuario_id = auth_user.id
        → PerfilUsuario.empresa_id → Empresa
    """

    def _get_empresa(self):
        """
        Obtiene la empresa del usuario autenticado siguiendo la cadena:
        request.user → PerfilUsuario → Empresa
        """
        user = self.request.user
        if not user or not user.is_authenticated:
            return None
        if user.is_superuser:
            return None
        try:
            # auth_user → perfil_usuario → empresa
            return user.perfil.empresa
        except Exception:
            return None

    def get_queryset(self):
        qs = super().get_queryset()
        empresa = self._get_empresa()
        if empresa is not None:
            qs = qs.filter(empresa=empresa)
        return qs

    def perform_create(self, serializer):
        # empresa es read_only en el serializer — solo el servidor la asigna
        empresa = self._get_empresa()
        serializer.save(empresa=empresa)

    def perform_update(self, serializer):
        empresa = self._get_empresa()
        serializer.save(empresa=empresa)


# ── ViewSets ──────────────────────────────────────────────────
class VariablesFijasView(EmpresaViewSetMixin, viewsets.ModelViewSet):
    queryset         = VariablesFijas.objects.all()
    serializer_class = VariablesFijasSerializer

    @action(
        detail=False, methods=["get"], url_path="para-cotizador",
        authentication_classes=[JWTAuthentication],
        permission_classes=[AllowAny],
    )
    def para_cotizador(self, request):
        """Devuelve las variables aplicables al cotizador público.
        - Autenticado con empresa → variables de esa empresa.
        - Anónimo o sin empresa   → variables generales (empresa=None).
        """
        obj = None
        if request.user and request.user.is_authenticated:
            try:
                empresa = request.user.perfil.empresa
                if empresa:
                    obj = VariablesFijas.objects.filter(empresa=empresa).first()
            except AttributeError:
                pass
        if obj is None:
            obj = VariablesFijas.objects.filter(empresa__isnull=True).first()
        if obj is None:
            return Response({"detail": "No hay Variables Fijas configuradas."}, status=404)
        return Response(VariablesFijasSerializer(obj).data)


class InventarioPiezaView(EmpresaViewSetMixin, viewsets.ModelViewSet):
    queryset         = InventarioPieza.objects.prefetch_related("imagenes")
    serializer_class = InventarioPiezaSerializer
    filter_backends  = [filters.SearchFilter, filters.OrderingFilter]
    search_fields    = ["nombre"]
    ordering_fields  = ["nombre", "precio_venta_sugerido", "costo_total_real"]

    @action(detail=True, methods=["get"], url_path="descargar-imagenes-ia")
    def descargar_imagenes_ia(self, request, pk=None):
        pieza    = self.get_object()
        imagenes = [img for img in pieza.imagenes.all() if img.imagen_procesada]
        if pieza.imagen_procesada:
            imagenes = list(imagenes) + [pieza]  # incluir imagen principal si la tiene
        if not imagenes:
            return Response({"detail": "Sin imágenes IA procesadas."}, status=404)

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, img in enumerate(imagenes, 1):
                try:
                    with open(img.imagen_procesada.path, "rb") as f:
                        zf.writestr(f"imagen_ia_{i:02d}.jpg", f.read())
                except OSError:
                    pass

        buf.seek(0)
        nombre_zip = "".join(c if c.isalnum() else "_" for c in pieza.nombre).lower()
        resp = HttpResponse(buf.read(), content_type="application/zip")
        resp["Content-Disposition"] = f'attachment; filename="{nombre_zip}_ia.zip"'
        return resp


class PedidoView(EmpresaViewSetMixin, viewsets.ModelViewSet):
    queryset         = Pedido.objects.select_related("cliente", "figura", "maquina")
    serializer_class = PedidoSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["estado", "prioridad", "maquina", "numero_pedido"]
    search_fields    = ["numero_pedido", "cliente__nombre", "figura__nombre", "descripcion"]
    ordering_fields  = ["fecha_entrega", "prioridad", "precio_unidad", "creado_en"]

    @action(detail=False, methods=["get"], url_path="dashboard")
    def dashboard(self, request):
        return Response(PedidoService.dashboard())

    @action(detail=True, methods=["patch"], url_path="cambiar-estado")
    def cambiar_estado(self, request, pk=None):
        nuevo_estado = request.data.get("estado")
        if not nuevo_estado:
            return Response({"error": "Campo 'estado' requerido."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            pedido = PedidoService.cambiar_estado(pk, nuevo_estado)
            return Response(PedidoSerializer(pedido).data)
        except Pedido.DoesNotExist:
            return Response({"error": "Pedido no encontrado."}, status=status.HTTP_404_NOT_FOUND)


class VentaView(EmpresaViewSetMixin, viewsets.ModelViewSet):
    queryset         = Venta.objects.prefetch_related("pedidos")
    serializer_class = VentaSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["fecha"]
    search_fields    = ["pedidos__numero_pedido"]
    ordering_fields  = ["fecha"]

    @action(detail=False, methods=["get"], url_path="resumen")
    def resumen(self, request):
        return Response(VentaService.resumen())


class TareaView(EmpresaViewSetMixin, viewsets.ModelViewSet):
    queryset         = Tarea.objects.select_related("pedido", "maquina")
    serializer_class = TareaSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["estado", "prioridad", "maquina"]
    search_fields    = ["producto", "cliente_texto", "descripcion"]
    ordering_fields  = ["fecha_entrega", "prioridad"]

    @action(detail=False, methods=["get"], url_path="pendientes")
    def pendientes(self, request):
        qs = TareaService.pendientes()
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=True, methods=["patch"], url_path="cambiar-estado")
    def cambiar_estado(self, request, pk=None):
        nuevo_estado = request.data.get("estado")
        if not nuevo_estado:
            return Response({"error": "Campo 'estado' requerido."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            tarea = TareaService.cambiar_estado(pk, nuevo_estado)
            return Response(TareaSerializer(tarea).data)
        except Tarea.DoesNotExist:
            return Response({"error": "Tarea no encontrada."}, status=status.HTTP_404_NOT_FOUND)


class FiguraView(EmpresaViewSetMixin, viewsets.ModelViewSet):
    queryset         = Figura.objects.prefetch_related("figura_piezas__pieza", "imagenes")
    serializer_class = FiguraSerializer
    filter_backends  = [filters.SearchFilter, filters.OrderingFilter]
    search_fields    = ["nombre", "descripcion"]
    ordering_fields  = ["nombre", "creado_en"]

    @action(
        detail=False, methods=["get"], url_path="publico",
        authentication_classes=[], permission_classes=[AllowAny],
    )
    def publico(self, request):
        """Catálogo público (dominio raíz): solo nombre, descripción, imágenes
        y precio total — sin costo ni desglose de piezas.

        Si viene ?cliente=<id>, el precio se incrementa según la comisión (%)
        de ese cliente, y si ese cliente tiene categorías configuradas en
        Cliente.categorias_visibles, el catálogo se filtra a solo esas
        categorías (sin ninguna configurada, se ven todas). El cliente nunca
        se expone en la respuesta, solo se usa para ajustar precio y filtro."""
        qs = Figura.objects.prefetch_related("imagenes", "categorias", "colores", "tipos").order_by("nombre")

        comision = None
        cliente_id = request.GET.get("cliente")
        if cliente_id:
            cliente = Cliente.objects.filter(pk=cliente_id).only("comision").first()
            if cliente:
                comision = cliente.comision
                categorias_ids = list(cliente.categorias_visibles.values_list("id", flat=True))
                if categorias_ids:
                    qs = qs.filter(categorias__id__in=categorias_ids).distinct()

        serializer = FiguraPublicaSerializer(qs, many=True, context={"request": request, "comision": comision})
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="descargar-imagenes-ia")
    def descargar_imagenes_ia(self, request, pk=None):
        figura   = self.get_object()
        imagenes = [img for img in figura.imagenes.all() if img.imagen_procesada]
        if not imagenes:
            return Response({"detail": "Sin imágenes IA procesadas."}, status=404)

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, img in enumerate(imagenes, 1):
                try:
                    with open(img.imagen_procesada.path, "rb") as f:
                        zf.writestr(f"imagen_ia_{i:02d}.jpg", f.read())
                except OSError:
                    pass

        buf.seek(0)
        nombre_zip = "".join(c if c.isalnum() else "_" for c in figura.nombre).lower()
        resp = HttpResponse(buf.read(), content_type="application/zip")
        resp["Content-Disposition"] = f'attachment; filename="{nombre_zip}_ia.zip"'
        return resp


class FiguraPiezaView(viewsets.ModelViewSet):
    queryset         = FiguraPieza.objects.select_related("figura", "pieza")
    serializer_class = FiguraPiezaSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        figura_id = self.request.query_params.get("figura")
        if figura_id:
            qs = qs.filter(figura_id=figura_id)
        return qs

    def perform_create(self, serializer):
        serializer.save()
