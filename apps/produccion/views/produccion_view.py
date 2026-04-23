"""
views/produccion_view.py
ViewSets para: VariablesFijas, InventarioPieza, Pedido, Venta, Tarea.
Responsabilidad: solo HTTP (rutas, status codes, respuestas).
Lógica de negocio → controllers/
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.produccion.models import VariablesFijas, InventarioPieza, Pedido, Venta, Tarea
from apps.produccion.controllers import (
    VariablesFijasSerializer,  VariablesFijasController,
    InventarioPiezaSerializer, InventarioController,
    PedidoSerializer,          PedidoController,
    VentaSerializer,           VentaController,
    TareaSerializer,           TareaController,
)


class VariablesFijasView(viewsets.ModelViewSet):
    """
    Singleton — solo existe el registro pk=1.
    Usar: GET/PATCH /api/v1/variables-fijas/1/
    """
    queryset         = VariablesFijas.objects.all()
    serializer_class = VariablesFijasSerializer


class InventarioPiezaView(viewsets.ModelViewSet):
    queryset         = InventarioPieza.objects.all()
    serializer_class = InventarioPiezaSerializer
    filter_backends  = [filters.SearchFilter, filters.OrderingFilter]
    search_fields    = ["nombre"]
    ordering_fields  = ["nombre", "precio_venta_sugerido", "costo_total_real"]


class PedidoView(viewsets.ModelViewSet):
    queryset         = Pedido.objects.select_related("cliente", "pieza", "material", "maquina")
    serializer_class = PedidoSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["estado", "prioridad", "maquina", "numero_pedido"]
    search_fields    = ["numero_pedido", "cliente__nombre", "pieza__nombre", "descripcion"]
    ordering_fields  = ["fecha_entrega", "prioridad", "precio_unidad", "creado_en"]

    @action(detail=False, methods=["get"], url_path="dashboard")
    def dashboard(self, request):
        return Response(PedidoController.dashboard())

    @action(detail=True, methods=["patch"], url_path="cambiar-estado")
    def cambiar_estado(self, request, pk=None):
        nuevo_estado = request.data.get("estado")
        if not nuevo_estado:
            return Response({"error": "Campo 'estado' requerido."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            pedido = PedidoController.cambiar_estado(pk, nuevo_estado)
            return Response(PedidoSerializer(pedido).data)
        except Pedido.DoesNotExist:
            return Response({"error": "Pedido no encontrado."}, status=status.HTTP_404_NOT_FOUND)


class VentaView(viewsets.ModelViewSet):
    queryset         = Venta.objects.select_related("cliente", "pedido")
    serializer_class = VentaSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["fecha", "cliente"]
    search_fields    = ["articulo"]
    ordering_fields  = ["fecha", "cantidad"]

    @action(detail=False, methods=["get"], url_path="resumen")
    def resumen(self, request):
        return Response(VentaController.resumen())


class TareaView(viewsets.ModelViewSet):
    queryset         = Tarea.objects.select_related("pedido", "maquina")
    serializer_class = TareaSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["estado", "prioridad", "maquina"]
    search_fields    = ["producto", "cliente_texto", "descripcion"]
    ordering_fields  = ["fecha_entrega", "prioridad"]

    @action(detail=False, methods=["get"], url_path="pendientes")
    def pendientes(self, request):
        qs = TareaController.pendientes()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["patch"], url_path="cambiar-estado")
    def cambiar_estado(self, request, pk=None):
        nuevo_estado = request.data.get("estado")
        if not nuevo_estado:
            return Response({"error": "Campo 'estado' requerido."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            tarea = TareaController.cambiar_estado(pk, nuevo_estado)
            return Response(TareaSerializer(tarea).data)
        except Tarea.DoesNotExist:
            return Response({"error": "Tarea no encontrada."}, status=status.HTTP_404_NOT_FOUND)
