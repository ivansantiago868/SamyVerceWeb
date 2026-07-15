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

# ── Paleta SamyVerse (Neon Voxel – Manual de Marca) ──────────────────────────
DEEP_SPACE   = HexColor("#1A1A2E")   # Fondo página
CARD_BG      = HexColor("#252540")   # Fondo tarjeta figura
CYBER_CYAN   = HexColor("#00E5FF")   # Títulos / headings
VOXEL_MAG    = HexColor("#D500F9")   # Acentos / separadores
GAMER_GREEN  = HexColor("#00FF9D")   # Precio / CTA
WHITE_TXT    = HexColor("#FFFFFF")   # Texto principal
GRAY_BODY    = HexColor("#B0B0C0")   # Texto secundario


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
    cell_w = ancho_disponible * 0.90
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


def _fondo_oscuro(canvas, doc):
    """Callback: pinta fondo Deep Space Blue en cada página y footer de marca."""
    PAGE_W, PAGE_H = A4
    canvas.saveState()
    # Fondo
    canvas.setFillColor(DEEP_SPACE)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # Línea inferior Magenta
    canvas.setStrokeColor(VOXEL_MAG)
    canvas.setLineWidth(2)
    canvas.line(0, 20, PAGE_W, 20)
    # Footer texto
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GRAY_BODY)
    canvas.drawCentredString(PAGE_W / 2, 8, f"Pág. {doc.page}  ·  www.samyverse3d.com  ·  UN UNIVERSO DE SORPRESAS")
    canvas.restoreState()


def _generar_pdf(figuras, nombre_empresa, empresa=None, usar_ia=True, mixto=False, categoria=None):
    """Construye el PDF del catálogo con identidad visual SamyVerse."""
    buf = io.BytesIO()
    PAGE_W, _ = A4
    MARGIN = 1.8 * cm
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=1.5 * cm,
    )
    ancho = PAGE_W - 2 * MARGIN

    styles = getSampleStyleSheet()

    # ── Estilos de marca ──────────────────────────────────────────────────────
    st_cover_title = ParagraphStyle("cover_title", parent=styles["Heading1"],
        fontSize=28, textColor=WHITE_TXT, alignment=TA_CENTER,
        fontName="Helvetica-Bold", spaceAfter=6, leading=34)
    st_cover_sub = ParagraphStyle("cover_sub", parent=styles["Normal"],
        fontSize=14, textColor=CYBER_CYAN, alignment=TA_CENTER, spaceAfter=4)
    st_cover_slogan = ParagraphStyle("cover_slogan", parent=styles["Normal"],
        fontSize=11, textColor=VOXEL_MAG, alignment=TA_CENTER,
        fontName="Helvetica-Oblique", spaceAfter=6)
    st_cover_url = ParagraphStyle("cover_url", parent=styles["Normal"],
        fontSize=10, textColor=GAMER_GREEN, alignment=TA_CENTER,
        fontName="Helvetica-Bold")
    st_nombre = ParagraphStyle("nombre_figura", parent=styles["Heading2"],
        fontSize=15, textColor=CYBER_CYAN, spaceBefore=4, spaceAfter=6,
        fontName="Helvetica-Bold", leading=18)
    st_precio = ParagraphStyle("precio", parent=styles["Normal"],
        fontSize=14, textColor=GAMER_GREEN, spaceBefore=8, spaceAfter=6,
        fontName="Helvetica-Bold")
    st_desc = ParagraphStyle("desc", parent=styles["Normal"],
        fontSize=9, textColor=GRAY_BODY, spaceAfter=6, leading=14)
    st_badge = ParagraphStyle("badge", parent=styles["Normal"],
        fontSize=8, textColor=GRAY_BODY, alignment=TA_CENTER, spaceAfter=4)
    st_categoria = ParagraphStyle("categoria", parent=styles["Heading1"],
        fontSize=18, textColor=VOXEL_MAG, alignment=TA_LEFT,
        fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=8)

    story = []

    # ── PORTADA ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 2.5 * cm))

    if empresa and empresa.logo:
        try:
            logo_buf, logo_ratio = _descargar_imagen(empresa.logo.url)
            if logo_buf:
                logo_w = 5 * cm * 3.20
                logo_h = logo_w * logo_ratio
                logo_img = Image(logo_buf, width=logo_w, height=logo_h)
                logo_img.hAlign = "CENTER"
                story.append(logo_img)
                story.append(Spacer(1, 0.8 * cm))
        except Exception:
            pass

    story.append(HRFlowable(width=ancho, color=VOXEL_MAG, thickness=2, spaceAfter=12))
    story.append(Paragraph("CATÁLOGO DE FIGURAS", st_cover_title))
    story.append(Paragraph(nombre_empresa, st_cover_sub))
    story.append(Paragraph("UN UNIVERSO DE SORPRESAS", st_cover_slogan))
    story.append(HRFlowable(width=ancho, color=CYBER_CYAN, thickness=1, spaceBefore=8, spaceAfter=12))

    total = figuras.count()
    story.append(Paragraph(
        f"{total} figura{'s' if total != 1 else ''} disponible{'s' if total != 1 else ''}",
        st_badge,
    ))
    if categoria:
        story.append(Paragraph(f"Categoría: {categoria.nombre}", st_badge))
    story.append(Paragraph("www.samyverse3d.com", st_cover_url))
    story.append(Spacer(1, 3 * cm))

    # ── FIGURAS ───────────────────────────────────────────────────────────────
    categoria_actual = object()  # centinela: distinto de cualquier categoría real
    for figura in figuras:
        # Si no se filtró a una sola categoría, agrupar el catálogo en secciones
        if not categoria and figura.categoria_id != categoria_actual:
            categoria_actual = figura.categoria_id
            nombre_categoria = figura.categoria.nombre if figura.categoria else "Sin categoría"
            story.append(Paragraph(nombre_categoria.upper(), st_categoria))
            story.append(HRFlowable(width=ancho, color=CYBER_CYAN, thickness=1, spaceAfter=8))

        # Cabecera de figura (nombre + acento) — mantenemos juntos
        story.append(KeepTogether([
            HRFlowable(width=ancho, color=VOXEL_MAG, thickness=2, spaceAfter=6),
            Paragraph(figura.nombre.upper(), st_nombre),
        ]))

        if figura.descripcion:
            story.append(Paragraph(figura.descripcion, st_desc))

        if mixto:
            for item in _collage_mixto(figura.imagenes.all(), ancho):
                story.append(item)
        else:
            collage = _collage(figura.imagenes.all(), ancho, usar_ia=usar_ia)
            if collage:
                story.append(collage)

        story.append(Paragraph(
            f"PRECIO DE VENTA: <b>${figura.precio_total:,.0f} COP</b>", st_precio,
        ))
        story.append(HRFlowable(width=ancho, color=CARD_BG, thickness=6, spaceAfter=4))
        story.append(Spacer(1, 0.3 * cm))

    doc.build(story, onFirstPage=_fondo_oscuro, onLaterPages=_fondo_oscuro)
    buf.seek(0)
    return buf


def _qs_y_empresa(request):
    from apps.produccion.models.empresa import Empresa
    from apps.produccion.models.figura import CategoriaFigura

    perfil = getattr(request.user, "perfil", None)
    qs = (
        Figura.objects
        .select_related("categoria")
        .prefetch_related("imagenes", "figura_piezas__pieza")
        .order_by("categoria__nombre", "nombre")
    )

    categoria = None
    categoria_id = request.GET.get("categoria__id__exact")
    if categoria_id:
        qs = qs.filter(categoria_id=categoria_id)
        categoria = CategoriaFigura.objects.filter(pk=categoria_id).first()

    if perfil and perfil.empresa_id:
        return qs.filter(empresa=perfil.empresa), str(perfil.empresa), perfil.empresa, categoria
    # Superadmin sin perfil: usar la primera empresa disponible para el logo
    empresa = Empresa.objects.filter(logo__isnull=False).exclude(logo="").first() \
              or Empresa.objects.first()
    nombre = str(empresa) if empresa else "Todas las empresas"
    return qs, nombre, empresa, categoria


@staff_member_required
def exportar_catalogo_pdf(request):
    """PDF con imágenes procesadas por IA."""
    figuras, nombre_empresa, empresa, categoria = _qs_y_empresa(request)
    buf = _generar_pdf(figuras, nombre_empresa, empresa=empresa, usar_ia=True, categoria=categoria)
    response = HttpResponse(buf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="catalogo_figuras_ia.pdf"'
    return response


@staff_member_required
def exportar_catalogo_pdf_real(request):
    """PDF con imágenes originales (sin procesamiento IA)."""
    figuras, nombre_empresa, empresa, categoria = _qs_y_empresa(request)
    buf = _generar_pdf(figuras, nombre_empresa, empresa=empresa, usar_ia=False, categoria=categoria)
    response = HttpResponse(buf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="catalogo_figuras.pdf"'
    return response


@staff_member_required
def exportar_catalogo_pdf_mixto(request):
    """PDF con imágenes originales e IA juntas para cada figura."""
    figuras, nombre_empresa, empresa, categoria = _qs_y_empresa(request)
    buf = _generar_pdf(figuras, nombre_empresa, empresa=empresa, mixto=True, categoria=categoria)
    response = HttpResponse(buf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="catalogo_figuras_mixto.pdf"'
    return response
