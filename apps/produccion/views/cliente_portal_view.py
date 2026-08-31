"""
views/cliente_portal_view.py
Portal del cliente en el catálogo público: login/logout con sesión de
Django (cookie propia, sin django.contrib.auth) y consulta de sus propios
pedidos.

No se usa django.contrib.auth.login(): así request.user sigue siendo
AnonymousUser y DRF's SessionAuthentication no exige CSRF en estos
endpoints públicos — mismo patrón que CarritoCheckoutView.
"""
from django.contrib.auth.hashers import check_password
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.produccion.models import Cliente, Pedido
from apps.produccion.serializers.cliente_portal import ClientePedidoSerializer

SESSION_KEY = "cliente_portal_id"
ERROR_CREDENCIALES = {"detail": "Documento o contraseña incorrectos."}


class ClienteLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        documento = (request.data.get("documento") or "").strip()
        password  = request.data.get("password") or ""
        if not documento or not password:
            return Response(ERROR_CREDENCIALES, status=status.HTTP_400_BAD_REQUEST)

        cliente = Cliente.objects.filter(documento=documento).exclude(password="").first()
        if not cliente or not check_password(password, cliente.password):
            return Response(ERROR_CREDENCIALES, status=status.HTTP_400_BAD_REQUEST)

        request.session[SESSION_KEY] = cliente.id
        return Response({"id": cliente.id, "nombre": cliente.nombre})


class ClienteLogoutView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        request.session.pop(SESSION_KEY, None)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClienteMeView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        cliente = _cliente_de_sesion(request)
        if not cliente:
            return Response({"detail": "No autenticado."}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({"id": cliente.id, "nombre": cliente.nombre})


class ClienteMisPedidosView(APIView):
    """Agrupa los Pedido del cliente por numero_pedido: una "orden" por
    checkout, con sus productos adentro. numero_pedido es el único campo
    compartido entre los Pedido de una misma compra (no hay FK a Venta)."""
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        cliente = _cliente_de_sesion(request)
        if not cliente:
            return Response({"detail": "No autenticado."}, status=status.HTTP_401_UNAUTHORIZED)

        pedidos = (
            Pedido.objects.filter(cliente_id=cliente.id)
            .select_related("figura", "color", "tipo")
            .prefetch_related("figura__imagenes")
            .order_by("-creado_en")
        )

        ordenes = {}
        for p in pedidos:
            clave = p.numero_pedido or f"pedido-{p.id}"
            orden = ordenes.get(clave)
            if orden is None:
                orden = ordenes[clave] = {
                    "numero_pedido": p.numero_pedido or None,
                    "fecha": p.creado_en,
                    "nombre_recibe": p.nombre_recibe,
                    "direccion_entrega": p.direccion_entrega,
                    "pedidos": [],
                }
            orden["pedidos"].append(p)
            if p.creado_en > orden["fecha"]:
                orden["fecha"] = p.creado_en

        data = [
            {
                "numero_pedido": o["numero_pedido"],
                "fecha": o["fecha"],
                "total": sum(p.precio_total for p in o["pedidos"]),
                "nombre_recibe": o["nombre_recibe"],
                "direccion_entrega": o["direccion_entrega"],
                "items": ClientePedidoSerializer(o["pedidos"], many=True).data,
            }
            for o in sorted(ordenes.values(), key=lambda o: o["fecha"], reverse=True)
        ]
        return Response(data)


def _cliente_de_sesion(request):
    cliente_id = request.session.get(SESSION_KEY)
    if not cliente_id:
        return None
    cliente = Cliente.objects.filter(pk=cliente_id).only("id", "nombre").first()
    if not cliente:
        request.session.pop(SESSION_KEY, None)
    return cliente
