import io
import zipfile

from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required

from PIL import Image as PILImage, ImageDraw, ImageFont

from apps.produccion.views.pdf_catalogo_figuras import (
    _qs_y_empresa, _descargar_imagen, _urls_por_modo, _resolver_cliente,
)

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


def _slug(texto, alterno):
    base = "".join(c if c.isalnum() else "_" for c in texto).lower().strip("_")
    return base or alterno


def _generar_zip_precios(request):
    """ZIP con TODAS las imágenes de cada figura (respeta los filtros activos
    del listado y lo elegido en el carrusel de cada imagen: Solo IA / Solo
    original / Ambas), cada una con el precio de venta superpuesto, y
    separadas en una carpeta por figura dentro del ZIP.

    Si viene ?cliente=<id>, el precio mostrado se incrementa según su %
    de comisión; sin ese parámetro, se usan los precios base de la empresa."""
    figuras, _nombre_empresa, _empresa, _categoria = _qs_y_empresa(request)
    _cliente_id, comision, _cliente_nombre = _resolver_cliente(request)

    buf_zip = io.BytesIO()
    carpetas_usadas = {}
    with zipfile.ZipFile(buf_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for figura in figuras:
            urls = _urls_por_modo(figura.imagenes.all())
            if not urls:
                continue

            precio = float(figura.precio_total)
            if comision:
                precio = round(precio * (1 + float(comision) / 100))

            carpeta_base = _slug(figura.nombre, f"figura_{figura.pk}")
            n_carpeta = carpetas_usadas.get(carpeta_base, 0) + 1
            carpetas_usadas[carpeta_base] = n_carpeta
            carpeta = carpeta_base if n_carpeta == 1 else f"{carpeta_base}_{n_carpeta}"

            for i, url in enumerate(urls, 1):
                imagen_buf, _ratio = _descargar_imagen(url)
                if not imagen_buf:
                    continue
                try:
                    final_buf = _con_precio(imagen_buf, precio)
                except Exception:
                    continue
                zf.writestr(f"{carpeta}/imagen_{i:02d}.jpg", final_buf.read())

    buf_zip.seek(0)
    response = HttpResponse(buf_zip.read(), content_type="application/zip")
    response["Content-Disposition"] = 'attachment; filename="figuras_precios.zip"'
    return response


@staff_member_required
def exportar_zip_precios(request):
    """ZIP (uso interno/admin) con el precio de venta superpuesto en cada imagen."""
    return _generar_zip_precios(request)


def exportar_zip_precios_publico(request):
    """Mismo ZIP, accesible sin sesión — para el botón de descarga del
    catálogo público en el dominio raíz. Con ?cliente=<id> ajusta el precio
    según su comisión; sin él, usa los precios base de la empresa."""
    return _generar_zip_precios(request)
