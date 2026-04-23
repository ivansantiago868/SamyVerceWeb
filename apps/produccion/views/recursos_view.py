"""
views/recursos_view.py
ViewSets para: Cliente, Impresora, Insumo, Gasto.
Responsabilidad: solo HTTP (rutas, status codes, respuestas).
Lógica de negocio → controllers/
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.produccion.models import Cliente, Impresora, Insumo, Gasto
from apps.produccion.controllers import (
    ClienteSerializer,   ClienteController,
    ImpresoraSerializer, ImpresoraController,
    InsumoSerializer,    InsumoController,
    GastoSerializer,     GastoController,
)


class ClienteView(viewsets.ModelViewSet):
    queryset         = Cliente.objects.all()
    serializer_class = ClienteSerializer
    filter_backends  = [filters.SearchFilter, filters.OrderingFilter]
    search_fields    = ["nombre", "email", "documento"]
    ordering_fields  = ["nombre", "creado_en"]


class ImpresoraView(viewsets.ModelViewSet):
    queryset         = Impresora.objects.all()
    serializer_class = ImpresoraSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["tipo", "activa"]
    search_fields    = ["nombre"]

    @action(detail=False, methods=["get"], url_path="activas")
    def activas(self, request):
        qs = ImpresoraController.activas()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class InsumoView(viewsets.ModelViewSet):
    queryset         = Insumo.objects.all()
    serializer_class = InsumoSerializer
    filter_backends  = [filters.SearchFilter]
    search_fields    = ["producto"]

    @action(detail=False, methods=["get"], url_path="stock-critico")
    def stock_critico(self, request):
        qs = InsumoController.stock_critico()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class GastoView(viewsets.ModelViewSet):
    queryset         = Gasto.objects.all()
    serializer_class = GastoSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["fecha"]
    search_fields    = ["articulo"]
    ordering_fields  = ["cuui", "fecha", "costo"]

    @action(detail=False, methods=["get"], url_path="resumen")
    def resumen(self, request):
        return Response(GastoController.resumen())
