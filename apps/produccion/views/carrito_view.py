"""
views/carrito_view.py
Checkout público del catálogo (sin pago).

POST /api/v1/carrito/checkout/
"""
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from apps.produccion.controllers.carrito_controller import CarritoController, CarritoError
from apps.produccion.serializers.carrito import CarritoCheckoutSerializer
from apps.produccion.views.cliente_portal_view import SESSION_KEY as CLIENTE_SESSION_KEY


class CarritoCheckoutView(APIView):
    """
    Recibe nombre y dirección de quien recibe más la lista de productos
    del carrito, y crea el Pedido (uno por producto), la Venta que los
    agrupa y el Cliente asociado. No procesa pago.

    Siempre público: si no se desactiva la autenticación de sesión, un
    visitante con sesión de admin activa en el mismo navegador (ej. un
    empleado revisando el catálogo) recibiría "CSRF token missing" al
    confirmar, porque DRF exige CSRF para usuarios de sesión autenticados.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CarritoCheckoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            resultado = CarritoController.confirmar_pedido(
                nombre_recibe=data["nombre_recibe"],
                direccion=data["direccion"],
                items=data["items"],
                cliente_id=request.session.get(CLIENTE_SESSION_KEY),
            )
        except CarritoError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(resultado, status=status.HTTP_201_CREATED)
