import io
import zipfile

from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required

from PIL import Image as PILImage, ImageDraw, ImageFont

from apps.produccion.views.pdf_catalogo_figuras import _qs_y_empresa, _descargar_imagen

# Rutas típicas del paquete fonts-dejavu-core en Debian/Ubuntu (imagen base del Dockerfile).
_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "DejaVuSans-Bold.ttf",
]

DEEP_SPACE  = (26, 26, 46, 215)     # Franja de precio (semi-transparente)
GAMER_GREEN = (0, 255, 157, 255)    # Texto de precio


def _cargar_fuente(tamano):
    for ruta in _FONT_PATHS:
        try:
            return ImageFont.truetype(ruta, tamano)
        except OSError:
            continue
    return ImageFont.load_default()


def _imagen_principal(figura):
    """Imagen a usar como portada: la IA si existe, si no la original."""
    primera = next(iter(figura.imagenes.all()), None)
    if not primera:
        return None
    return primera.imagen_procesada if primera.imagen_procesada else primera.imagen


def _con_precio(imagen_buf, precio):
    """Superpone una franja con el precio en la parte inferior de la imagen."""
    img = PILImage.open(imagen_buf).convert("RGB")
    w, h = img.size

    franja_h = max(int(h * 0.12), 48)
    franja = PILImage.new("RGBA", (w, franja_h), DEEP_SPACE)
    draw = ImageDraw.Draw(franja)

    texto = f"${precio:,.0f} COP"
    font = _cargar_fuente(max(int(franja_h * 0.45), 16))
    bbox = draw.textbbox((0, 0), texto, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((w - tw) / 2 - bbox[0], (franja_h - th) / 2 - bbox[1]), texto, fill=GAMER_GREEN, font=font)

    img.paste(franja, (0, h - franja_h), franja)

    salida = io.BytesIO()
    img.save(salida, format="JPEG", quality=90)
    salida.seek(0)
    return salida


@staff_member_required
def exportar_zip_precios(request):
    """ZIP con la imagen principal de cada figura (respeta los filtros activos del listado),
    con el precio de venta superpuesto en cada imagen."""
    figuras, _nombre_empresa, _empresa, _categoria = _qs_y_empresa(request)

    buf_zip = io.BytesIO()
    usados = {}
    with zipfile.ZipFile(buf_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for figura in figuras:
            campo = _imagen_principal(figura)
            if not campo:
                continue

            imagen_buf, _ratio = _descargar_imagen(campo.url)
            if not imagen_buf:
                continue

            try:
                final_buf = _con_precio(imagen_buf, figura.precio_total)
            except Exception:
                continue

            base = "".join(c if c.isalnum() else "_" for c in figura.nombre).lower() or f"figura_{figura.pk}"
            n = usados.get(base, 0) + 1
            usados[base] = n
            nombre_archivo = f"{base}.jpg" if n == 1 else f"{base}_{n}.jpg"
            zf.writestr(nombre_archivo, final_buf.read())

    buf_zip.seek(0)
    response = HttpResponse(buf_zip.read(), content_type="application/zip")
    response["Content-Disposition"] = 'attachment; filename="figuras_precios.zip"'
    return response
