"""
views/recursos_view.py
ViewSets para: Cliente, Impresora, Insumo, Gasto.
Responsabilidad: solo HTTP (rutas, status codes, respuestas).
Lógica de negocio → services/  |  Serialización → serializers/
"""
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.produccion.models import Cliente, Impresora, Insumo, Gasto
from apps.produccion.serializers import (
    ClienteSerializer, ImpresoraSerializer,
    InsumoSerializer, GastoSerializer,
)
from apps.produccion.services import (
    ImpresoraService, InsumoService, GastoService,
)
from apps.produccion.views.produccion_view import EmpresaViewSetMixin


class ClienteView(EmpresaViewSetMixin, viewsets.ModelViewSet):
    queryset         = Cliente.objects.all()
    serializer_class = ClienteSerializer
    filter_backends  = [filters.SearchFilter, filters.OrderingFilter]
    search_fields    = ["nombre", "email", "documento"]
    ordering_fields  = ["nombre", "creado_en"]


class ImpresoraView(EmpresaViewSetMixin, viewsets.ModelViewSet):
    queryset         = Impresora.objects.all()
    serializer_class = ImpresoraSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["tipo", "activa"]
    search_fields    = ["nombre"]

    @action(detail=False, methods=["get"], url_path="activas")
    def activas(self, request):
        qs = ImpresoraService.activas()
        return Response(self.get_serializer(qs, many=True).data)


class InsumoView(EmpresaViewSetMixin, viewsets.ModelViewSet):
    queryset         = Insumo.objects.all()
    serializer_class = InsumoSerializer
    filter_backends  = [filters.SearchFilter]
    search_fields    = ["producto"]

    @action(detail=False, methods=["get"], url_path="stock-critico")
    def stock_critico(self, request):
        qs = InsumoService.stock_critico()
        return Response(self.get_serializer(qs, many=True).data)


class GastoView(EmpresaViewSetMixin, viewsets.ModelViewSet):
    queryset         = Gasto.objects.all()
    serializer_class = GastoSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["fecha"]
    search_fields    = ["articulo"]
    ordering_fields  = ["cuui", "fecha", "costo"]

    @action(detail=False, methods=["get"], url_path="resumen")
    def resumen(self, request):
        return Response(GastoService.resumen())
