import io
import requests
from PIL import Image as PILImage

from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.admin.views.decorators import staff_member_required

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    Table, TableStyle, HRFlowable, KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from apps.produccion.models.figura import Figura

# ── Paleta ────────────────────────────────────────────────────────────────────
AZUL      = HexColor("#1a4b8c")
AZUL_CLARO = HexColor("#e8eef7")
GRIS      = HexColor("#555555")
PRECIO    = HexColor("#1a7a3c")


def _descargar_imagen(url, max_size=(400, 400)):
    """Descarga una imagen desde Drive y devuelve un objeto PIL redimensionado."""
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        img = PILImage.open(io.BytesIO(r.content)).convert("RGB")
        img.thumbnail(max_size, PILImage.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        buf.seek(0)
        return buf
    except Exception:
        return None


def _collage(imagenes_qs, ancho_disponible, usar_ia=True):
    """
    Genera una tabla-collage con máximo 5 imágenes.
    usar_ia=True  → imagen procesada por IA (o real como fallback)
    usar_ia=False → imagen real original
    """
    imgs_url = []
    for fi in imagenes_qs[:5]:
        if usar_ia:
            url = fi.imagen_procesada.url if fi.imagen_procesada else (fi.imagen.url if fi.imagen else None)
        else:
            url = fi.imagen.url if fi.imagen else None
        if url:
            imgs_url.append(url)

    if not imgs_url:
        return None

    n = len(imgs_url)

    # Tamaño base (3 columnas) × 1.50 → imágenes 50% más grandes
    cell_w = ((ancho_disponible / 3) - 0.3 * cm) * 2.50
    cell_h = cell_w * 0.75
    col_total = cell_w + 0.3 * cm

    # Cuántas columnas caben con el nuevo tamaño
    columnas = min(n, max(1, int(ancho_disponible / col_total)))

    filas_datos = []
    fila_actual = []
    for i, url in enumerate(imgs_url):
        buf = _descargar_imagen(url)
        if buf:
            img_obj = Image(buf, width=cell_w, height=cell_h)
        else:
            img_obj = Paragraph("—", getSampleStyleSheet()["Normal"])
        fila_actual.append(img_obj)
        if len(fila_actual) == columnas:
            filas_datos.append(fila_actual)
            fila_actual = []
    if fila_actual:
        while len(fila_actual) < columnas:
            fila_actual.append("")
        filas_datos.append(fila_actual)

    col_widths = [col_total] * columnas
    tabla = Table(filas_datos, colWidths=col_widths, rowHeights=[cell_h + 0.3 * cm] * len(filas_datos))
    tabla.setStyle(TableStyle([
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",        (0, 0), (-1, -1), 0.5, HexColor("#dddddd")),
        ("BACKGROUND",  (0, 0), (-1, -1), HexColor("#f8f8f8")),
        ("ROWPADDING",  (0, 0), (-1, -1), 4),
    ]))
    return tabla


def _collage_mixto(imagenes_qs, ancho_disponible):
    """
    Devuelve una lista de flowables con dos filas:
    etiqueta + collage de originales, luego etiqueta + collage de IA.
    """
    styles = getSampleStyleSheet()
    st_label = ParagraphStyle(
        "label_mixto", parent=styles["Normal"],
        fontSize=8, textColor=HexColor("#888888"),
        spaceBefore=4, spaceAfter=2,
    )
    bloques = []
    datos = [
        ("Foto original", False),
        ("Foto IA",       True),
    ]
    for etiqueta, usar_ia in datos:
        col = _collage(imagenes_qs, ancho_disponible, usar_ia=usar_ia)
        if col:
            bloques.append(Paragraph(etiqueta, st_label))
            bloques.append(col)
    return bloques


def _generar_pdf(figuras, nombre_empresa, usar_ia=True, mixto=False):
    """Construye el PDF del catálogo y devuelve un BytesIO listo para enviar."""
    buf = io.BytesIO()
    PAGE_W, _ = A4
    MARGIN = 2 * cm
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
    )
    ancho = PAGE_W - 2 * MARGIN

    styles = getSampleStyleSheet()
    st_titulo = ParagraphStyle("titulo", parent=styles["Heading1"],
        fontSize=22, textColor=AZUL, alignment=TA_CENTER, spaceAfter=4)
    st_empresa = ParagraphStyle("empresa", parent=styles["Normal"],
        fontSize=11, textColor=GRIS, alignment=TA_CENTER, spaceAfter=20)
    st_nombre = ParagraphStyle("nombre_figura", parent=styles["Heading2"],
        fontSize=14, textColor=AZUL, spaceBefore=14, spaceAfter=4)
    st_precio = ParagraphStyle("precio", parent=styles["Normal"],
        fontSize=13, textColor=PRECIO, spaceBefore=6, spaceAfter=4,
        fontName="Helvetica-Bold")
    st_desc = ParagraphStyle("desc", parent=styles["Normal"],
        fontSize=9, textColor=GRIS, spaceAfter=4)

    story = []
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("Catálogo de Figuras", st_titulo))
    story.append(Paragraph(nombre_empresa, st_empresa))
    story.append(HRFlowable(width=ancho, color=AZUL, thickness=2))
    story.append(Spacer(1, 0.5 * cm))

    total = figuras.count()
    story.append(Paragraph(
        f"{total} figura{'s' if total != 1 else ''} disponible{'s' if total != 1 else ''}",
        st_empresa,
    ))
    story.append(Spacer(1, 2 * cm))

    for figura in figuras:
        bloque = []
        bloque.append(Paragraph(figura.nombre, st_nombre))
        if figura.descripcion:
            bloque.append(Paragraph(figura.descripcion, st_desc))
        if mixto:
            bloque.extend(_collage_mixto(figura.imagenes.all(), ancho))
        else:
            collage = _collage(figura.imagenes.all(), ancho, usar_ia=usar_ia)
            if collage:
                bloque.append(collage)
        bloque.append(Paragraph(
            f"Precio de venta: <b>${figura.precio_total:,.0f}</b>", st_precio,
        ))
        bloque.append(HRFlowable(width=ancho, color=HexColor("#cccccc"), thickness=0.5))
        bloque.append(Spacer(1, 0.3 * cm))
        story.append(KeepTogether(bloque))

    doc.build(story)
    buf.seek(0)
    return buf


def _qs_y_empresa(request):
    perfil = getattr(request.user, "perfil", None)
    qs = Figura.objects.prefetch_related("imagenes", "figura_piezas__pieza").order_by("nombre")
    if perfil and perfil.empresa_id:
        return qs.filter(empresa=perfil.empresa), str(perfil.empresa)
    return qs, "Todas las empresas"


@staff_member_required
def exportar_catalogo_pdf(request):
    """PDF con imágenes procesadas por IA."""
    figuras, nombre_empresa = _qs_y_empresa(request)
    buf = _generar_pdf(figuras, nombre_empresa, usar_ia=True)
    response = HttpResponse(buf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="catalogo_figuras_ia.pdf"'
    return response


@staff_member_required
def exportar_catalogo_pdf_real(request):
    """PDF con imágenes originales (sin procesamiento IA)."""
    figuras, nombre_empresa = _qs_y_empresa(request)
    buf = _generar_pdf(figuras, nombre_empresa, usar_ia=False)
    response = HttpResponse(buf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="catalogo_figuras.pdf"'
    return response


@staff_member_required
def exportar_catalogo_pdf_mixto(request):
    """PDF con imágenes originales e IA juntas para cada figura."""
    figuras, nombre_empresa = _qs_y_empresa(request)
    buf = _generar_pdf(figuras, nombre_empresa, mixto=True)
    response = HttpResponse(buf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="catalogo_figuras_mixto.pdf"'
    return response
