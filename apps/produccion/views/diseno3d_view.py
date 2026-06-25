"""
views/diseno3d_view.py
Endpoints para generación de modelos 3D con Tripo AI.

POST /api/v1/diseno3d/          → crea diseño + lanza generación
GET  /api/v1/diseno3d/          → lista diseños de la empresa
GET  /api/v1/diseno3d/{id}/     → detalle + estado + URL de descarga
"""
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from apps.produccion.controllers.diseno3d_controller import Diseno3DController
from apps.produccion.models.diseno3d import Diseno3D
from apps.produccion.serializers.diseno3d import (
    Diseno3DEstadoSerializer,
    Diseno3DInputSerializer,
    Diseno3DListSerializer,
)


def _empresa_de_usuario(user):
    try:
        return user.perfilusuario.empresa
    except Exception:
        return None


class Diseno3DCrearView(APIView):
    """
    POST /api/v1/diseno3d/
    Crea un Diseno3D, sube la imagen a Tripo AI y lanza la generación en segundo plano.
    Retorna id + estado inicial para que el cliente haga polling.
    """
    permission_classes = [AllowAny]
    parser_classes     = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = Diseno3DInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data    = serializer.validated_data
        empresa = _empresa_de_usuario(request.user) if request.user.is_authenticated else None
        usuario = request.user if request.user.is_authenticated else None

        diseno = Diseno3D.objects.create(
            empresa              = empresa,
            usuario              = usuario,
            nombre               = data.get("nombre", ""),
            imagen_original      = data["imagen"],
            model_version        = data["model_version"],
            formato              = data["formato"],
            texture              = data["texture"],
            pbr                  = data["pbr"],
            face_limit           = data["face_limit"],
            texture_alignment    = data["texture_alignment"],
            orientation          = data["orientation"],
            enable_image_autofix = data["enable_image_autofix"],
            prompt               = data.get("prompt", ""),
            estado               = "procesando",
        )

        try:
            Diseno3DController.iniciar_generacion(diseno)
        except Exception as exc:
            diseno.estado        = "fallido"
            diseno.error_mensaje = str(exc)
            diseno.save(update_fields=["estado", "error_mensaje"])
            return Response(
                {"error": str(exc), "id": diseno.pk},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "id":      diseno.pk,
                "estado":  "procesando",
                "mensaje": f"Generación iniciada. Consulta el estado en /api/v1/diseno3d/{diseno.pk}/",
            },
            status=status.HTTP_201_CREATED,
        )


class Diseno3DListView(APIView):
    """
    GET /api/v1/diseno3d/
    Lista los diseños 3D de la empresa del usuario autenticado.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        empresa = _empresa_de_usuario(request.user)
        qs = Diseno3D.objects.filter(empresa=empresa).order_by("-creado_en")
        serializer = Diseno3DListSerializer(qs, many=True)
        return Response(serializer.data)


class Diseno3DDetalleView(APIView):
    """
    GET /api/v1/diseno3d/{pk}/
    Retorna el estado actual, progreso y URL del modelo si está listo.
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        empresa = _empresa_de_usuario(request.user) if request.user.is_authenticated else None
        try:
            estado = Diseno3DController.get_estado(pk, empresa=empresa)
            return Response(estado)
        except LookupError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)
