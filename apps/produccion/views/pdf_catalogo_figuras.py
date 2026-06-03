import io
import requests
from PIL import Image as PILImage  # noqa: F401 usado en _collage

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


def _descargar_imagen(url):
    """Descarga una imagen desde Drive y devuelve (BytesIO, aspect_ratio)."""
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.content
        with PILImage.open(io.BytesIO(data)) as img:
            w, h = img.size
            ratio = h / w if w > 0 else 1.0
        buf = io.BytesIO(data)
        buf.seek(0)
        return buf, ratio
    except Exception:
        return None, 1.0


def _collage(imagenes_qs, ancho_disponible, usar_ia=True):
    """
    Genera una tabla-collage con máximo 5 imágenes.
    Ajusta el alto de cada fila según el aspecto real de las imágenes.
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

    # Descargar todas las imágenes y obtener sus ratios reales
    descargadas = [_descargar_imagen(url) for url in imgs_url]
    descargadas = [(buf, ratio) for buf, ratio in descargadas if buf is not None]
    if not descargadas:
        return None

    n = len(descargadas)
    cell_w = ancho_disponible * 0.40
    col_total = cell_w + 0.3 * cm
    columnas = min(n, max(1, int(ancho_disponible / col_total)))

    # Agrupar en filas y calcular alto por fila (máximo ratio de la fila)
    filas_datos = []
    filas_alturas = []
    fila_actual = []
    ratios_fila = []

    for buf, ratio in descargadas:
        fila_actual.append((buf, ratio))
        ratios_fila.append(ratio)
        if len(fila_actual) == columnas:
            max_ratio = max(ratios_fila)
            cell_h = cell_w * max_ratio
            fila_imgs = []
            for b, _ in fila_actual:
                fila_imgs.append(Image(b, width=cell_w, height=cell_h))
            filas_datos.append(fila_imgs)
            filas_alturas.append(cell_h + 0.3 * cm)
            fila_actual = []
            ratios_fila = []

    if fila_actual:
        max_ratio = max(ratios_fila) if ratios_fila else 1.0
        cell_h = cell_w * max_ratio
        fila_imgs = []
        for b, _ in fila_actual:
            fila_imgs.append(Image(b, width=cell_w, height=cell_h))
        while len(fila_imgs) < columnas:
            fila_imgs.append("")
        filas_datos.append(fila_imgs)
        filas_alturas.append(cell_h + 0.3 * cm)

    col_widths = [col_total] * columnas
    tabla = Table(filas_datos, colWidths=col_widths, rowHeights=filas_alturas)
    tabla.setStyle(TableStyle([
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",       (0, 0), (-1, -1), 0.5, HexColor("#dddddd")),
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#f8f8f8")),
        ("ROWPADDING", (0, 0), (-1, -1), 4),
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


def _generar_pdf(figuras, nombre_empresa, empresa=None, usar_ia=True, mixto=False):
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
    story.append(Spacer(1, 2 * cm))

    # Logo de la empresa
    if empresa and empresa.logo:
        try:
            logo_buf, logo_ratio = _descargar_imagen(empresa.logo.url)
            if logo_buf:
                logo_w = 5 * cm
                logo_h = logo_w * logo_ratio
                logo_img = Image(logo_buf, width=logo_w, height=logo_h)
                logo_img.hAlign = "CENTER"
                story.append(logo_img)
                story.append(Spacer(1, 0.5 * cm))
        except Exception:
            pass

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
    from apps.produccion.models.empresa import Empresa
    perfil = getattr(request.user, "perfil", None)
    qs = Figura.objects.prefetch_related("imagenes", "figura_piezas__pieza").order_by("nombre")
    if perfil and perfil.empresa_id:
        return qs.filter(empresa=perfil.empresa), str(perfil.empresa), perfil.empresa
    # Superadmin sin perfil: usar la primera empresa disponible para el logo
    empresa = Empresa.objects.filter(logo__isnull=False).exclude(logo="").first() \
              or Empresa.objects.first()
    nombre = str(empresa) if empresa else "Todas las empresas"
    return qs, nombre, empresa


@staff_member_required
def exportar_catalogo_pdf(request):
    """PDF con imágenes procesadas por IA."""
    figuras, nombre_empresa, empresa = _qs_y_empresa(request)
    buf = _generar_pdf(figuras, nombre_empresa, empresa=empresa, usar_ia=True)
    response = HttpResponse(buf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="catalogo_figuras_ia.pdf"'
    return response


@staff_member_required
def exportar_catalogo_pdf_real(request):
    """PDF con imágenes originales (sin procesamiento IA)."""
    figuras, nombre_empresa, empresa = _qs_y_empresa(request)
    buf = _generar_pdf(figuras, nombre_empresa, empresa=empresa, usar_ia=False)
    response = HttpResponse(buf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="catalogo_figuras.pdf"'
    return response


@staff_member_required
def exportar_catalogo_pdf_mixto(request):
    """PDF con imágenes originales e IA juntas para cada figura."""
    figuras, nombre_empresa, empresa = _qs_y_empresa(request)
    buf = _generar_pdf(figuras, nombre_empresa, empresa=empresa, mixto=True)
    response = HttpResponse(buf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="catalogo_figuras_mixto.pdf"'
    return response
