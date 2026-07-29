from rest_framework import serializers
from apps.produccion.models import Figura, FiguraImagen, FiguraPieza


def _url_absoluta(campo, request):
    if not campo:
        return None
    try:
        url = campo.url
        return request.build_absolute_uri(url) if request else url
    except Exception:
        return None


def _imagenes_aplanadas(figura, request):
    """Aplana las imágenes de una figura a una lista de slides para el carrusel.
    Cada FiguraImagen aporta 1 slide (IA o normal) o 2 si su modo es "ambas"."""
    resultado = []
    for img in figura.imagenes.all():
        url_ia     = _url_absoluta(img.imagen_procesada, request)
        url_normal = _url_absoluta(img.imagen, request)

        if img.modo_carrusel == FiguraImagen.AMBAS:
            urls = [u for u in (url_ia, url_normal) if u]
        elif img.modo_carrusel == FiguraImagen.NORMAL:
            urls = [url_normal] if url_normal else []
        else:  # IA (default): usar la IA si existe, si no caer a la normal.
            urls = [url_ia] if url_ia else ([url_normal] if url_normal else [])

        for url in urls:
            resultado.append({"id": img.id, "imagen": url, "orden": img.orden})
    return resultado


class FiguraPiezaSerializer(serializers.ModelSerializer):
    pieza_nombre    = serializers.ReadOnlyField(source="pieza.nombre")
    pieza_costo     = serializers.ReadOnlyField(source="pieza.costo_total_real")
    pieza_precio    = serializers.ReadOnlyField(source="pieza.precio_venta_sugerido")
    insumo_nombre   = serializers.CharField(source="insumo.producto", read_only=True)
    subtotal_costo  = serializers.ReadOnlyField()
    subtotal_precio = serializers.ReadOnlyField()

    class Meta:
        model  = FiguraPieza
        fields = [
            "id", "figura", "pieza", "pieza_nombre",
            "pieza_costo", "pieza_precio",
            "insumo", "insumo_nombre",
            "cantidad", "subtotal_costo", "subtotal_precio",
        ]
        read_only_fields = ("figura",)


class FiguraSerializer(serializers.ModelSerializer):
    figura_piezas = FiguraPiezaSerializer(many=True, read_only=True)
    imagenes      = serializers.SerializerMethodField()
    costo_total   = serializers.ReadOnlyField()
    precio_total  = serializers.ReadOnlyField()
    total_piezas  = serializers.ReadOnlyField()

    class Meta:
        model  = Figura
        fields = [
            "id", "nombre", "descripcion",
            "imagenes", "costo_total", "precio_total", "total_piezas",
            "figura_piezas", "creado_en", "actualizado_en",
        ]
        read_only_fields = ("empresa",)

    def get_imagenes(self, obj):
        return _imagenes_aplanadas(obj, self.context.get("request"))


class FiguraPublicaSerializer(serializers.ModelSerializer):
    """Serializer para el catálogo público (dominio raíz): solo lo que puede
    ver un visitante — nombre, descripción, imágenes y precio total. Nunca
    expone costo_total ni el desglose de figura_piezas (son datos internos
    de margen/costo del negocio)."""
    imagenes     = serializers.SerializerMethodField()
    precio_total = serializers.ReadOnlyField()

    class Meta:
        model  = Figura
        fields = ["id", "nombre", "descripcion", "imagenes", "precio_total"]

    def get_imagenes(self, obj):
        return _imagenes_aplanadas(obj, self.context.get("request"))
