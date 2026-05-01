"""
views/produccion_view.py
ViewSets para: VariablesFijas, InventarioPieza, Pedido, Venta, Tarea.
Responsabilidad: solo HTTP (rutas, status codes, respuestas).
Lógica de negocio → controllers/
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_filters.rest_framework import DjangoFilterBackend

from apps.produccion.models import VariablesFijas, InventarioPieza, Pedido, Venta, Tarea, Figura, FiguraPieza
from apps.produccion.serializers import (
    VariablesFijasSerializer, InventarioPiezaSerializer,
    PedidoSerializer, VentaSerializer, TareaSerializer,
    FiguraSerializer, FiguraPiezaSerializer,
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
    queryset         = InventarioPieza.objects.all()
    serializer_class = InventarioPiezaSerializer
    filter_backends  = [filters.SearchFilter, filters.OrderingFilter]
    search_fields    = ["nombre"]
    ordering_fields  = ["nombre", "precio_venta_sugerido", "costo_total_real"]


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
    queryset         = Figura.objects.prefetch_related("figura_piezas__pieza")
    serializer_class = FiguraSerializer
    filter_backends  = [filters.SearchFilter, filters.OrderingFilter]
    search_fields    = ["nombre", "descripcion"]
    ordering_fields  = ["nombre", "creado_en"]


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
