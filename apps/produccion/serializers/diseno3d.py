from rest_framework import serializers

from apps.produccion.models.diseno3d import Diseno3D


class Diseno3DInputSerializer(serializers.Serializer):
    """Campos recibidos al crear un diseño 3D."""
    imagen               = serializers.ImageField()
    nombre               = serializers.CharField(max_length=255, required=False, default="")
    model_version        = serializers.CharField(max_length=50,  required=False, default="P1-20260311")
    formato              = serializers.ChoiceField(
                               choices=[c[0] for c in Diseno3D.FORMATOS],
                               required=False, default="glb")
    texture              = serializers.BooleanField(required=False, default=True)
    pbr                  = serializers.BooleanField(required=False, default=True)
    face_limit           = serializers.IntegerField(min_value=100, max_value=200000,
                                                    required=False, default=20000)
    texture_alignment    = serializers.ChoiceField(
                               choices=[c[0] for c in Diseno3D.TEXTURE_ALIGN],
                               required=False, default="original_image")
    orientation          = serializers.ChoiceField(
                               choices=[c[0] for c in Diseno3D.ORIENTACIONES],
                               required=False, default="align_image")
    enable_image_autofix = serializers.BooleanField(required=False, default=True)
    prompt               = serializers.CharField(required=False, default="", allow_blank=True)


class Diseno3DEstadoSerializer(serializers.ModelSerializer):
    url_modelo = serializers.SerializerMethodField()

    class Meta:
        model  = Diseno3D
        fields = [
            "id", "nombre", "estado", "progreso", "error_mensaje",
            "tripo_task_id", "analisis_ia", "url_modelo",
            "creado_en", "actualizado_en",
        ]

    def get_url_modelo(self, obj):
        if obj.estado == "completado" and obj.archivo_modelo:
            try:
                return obj.archivo_modelo.url
            except Exception:
                return None
        return None


class Diseno3DListSerializer(serializers.ModelSerializer):
    url_imagen   = serializers.SerializerMethodField()
    url_modelo   = serializers.SerializerMethodField()

    class Meta:
        model  = Diseno3D
        fields = [
            "id", "nombre", "estado", "progreso",
            "formato", "url_imagen", "url_modelo",
            "creado_en",
        ]

    def get_url_imagen(self, obj):
        if obj.imagen_original:
            try:
                return obj.imagen_original.url
            except Exception:
                return None
        return None

    def get_url_modelo(self, obj):
        if obj.estado == "completado" and obj.archivo_modelo:
            try:
                return obj.archivo_modelo.url
            except Exception:
                return None
        return None
