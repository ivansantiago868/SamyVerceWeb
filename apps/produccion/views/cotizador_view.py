"""
views/cotizador_view.py
Endpoints HTTP del Cotizador.
Responsabilidad: validar input, delegar al CotizadorController, devolver respuesta.
Lógica matemática → services/cotizador.py
Orquestación      → controllers/cotizador_controller.py
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.produccion.serializers import (
    CotizadorInputSerializer,
    CotizadorLoteInputSerializer,
    CotizadorDesdeCatalogoSerializer,
    CotizadorDesdeCatalogoLoteSerializer,
)
from apps.produccion.controllers.cotizador_controller import CotizadorController


class CotizadorRecursosView(APIView):
    """
    GET /api/v1/cotizador/recursos/
    Devuelve las impresoras activas e insumos de la empresa del usuario logueado.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        recursos = CotizadorController.get_recursos(request.user)
        return Response(recursos, status=status.HTTP_200_OK)


class CotizadorView(APIView):
    permission_classes = [AllowAny]
    """
    POST /api/v1/cotizador/
    Calcula el precio de venta para una pieza nueva.
    Campos opcionales: impresora_id, insumo_id (solo aplican si el usuario está logueado).
    """

    def post(self, request):
        serializer = CotizadorInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            resultado = CotizadorController.cotizar_pieza(serializer.validated_data, user=request.user)
            return Response(resultado, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_424_FAILED_DEPENDENCY)


class CotizadorLoteView(APIView):
    permission_classes = [AllowAny]
    """
    POST /api/v1/cotizador/lote/
    Cotiza una pieza y escala el resultado por cantidad.
    """

    def post(self, request):
        serializer = CotizadorLoteInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            resultado = CotizadorController.cotizar_lote(serializer.validated_data, user=request.user)
            return Response(resultado, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_424_FAILED_DEPENDENCY)


class CotizadorDesdeCatalogoView(APIView):
    permission_classes = [AllowAny]
    """
    POST /api/v1/cotizador/desde-catalogo/
    Recalcula el precio de una pieza ya registrada en el Inventario.
    """

    def post(self, request):
        serializer = CotizadorDesdeCatalogoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            resultado = CotizadorController.cotizar_desde_catalogo(serializer.validated_data, user=request.user)
            return Response(resultado, status=status.HTTP_200_OK)
        except LookupError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_424_FAILED_DEPENDENCY)


class CotizadorDesdeCatalogoLoteView(APIView):
    permission_classes = [AllowAny]
    """
    POST /api/v1/cotizador/desde-catalogo/lote/
    Recalcula una pieza del catálogo y escala por cantidad.
    """

    def post(self, request):
        serializer = CotizadorDesdeCatalogoLoteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            resultado = CotizadorController.cotizar_lote_desde_catalogo(serializer.validated_data, user=request.user)
            return Response(resultado, status=status.HTTP_200_OK)
        except LookupError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_424_FAILED_DEPENDENCY)
