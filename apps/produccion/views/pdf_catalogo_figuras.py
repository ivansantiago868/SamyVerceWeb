import io
import requests
from PIL import Image as PILImage  # noqa: F401 usado en _collage

from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.admin.views.decorators import staff_member_required

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    Table, TableStyle, HRFlowable, Flowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase.pdfmetrics import stringWidth

from apps.produccion.models.figura import Figura, FiguraImagen

# ── Paleta SamyVerse (Neon Voxel – Manual de Marca), sobre fondo rosa claro ──
BG_PAGINA      = HexColor("#FDF1F5")   # Fondo de página (rosa muy claro)
DEEP_SPACE     = HexColor("#1A1A2E")   # Texto principal (título de portada)
CYBER_CYAN     = HexColor("#00E5FF")   # Líneas / acentos (neón de marca)
CYBER_CYAN_TXT = HexColor("#0086A3")   # Variante oscura para texto (contraste sobre blanco)
VOXEL_MAG      = HexColor("#D500F9")   # Líneas / acentos (neón de marca)
VOXEL_MAG_TXT  = HexColor("#9B00B8")   # Variante oscura para texto
GAMER_GREEN    = HexColor("#0A8F55")   # Precio / CTA (oscurecido para legibilidad sobre blanco)
GRAY_BODY      = HexColor("#5A5A6E")   # Texto secundario (oscurecido para legibilidad sobre blanco)

# ── Estilos de las tarjetas de producto (grilla 2 columnas: foto + texto) ────
_st_card_nombre = ParagraphStyle(
    "card_nombre", fontName="Helvetica-Bold", fontSize=11,
    textColor=CYBER_CYAN_TXT, leading=13, spaceAfter=3,
)
_st_card_desc = ParagraphStyle(
    "card_desc", fontName="Helvetica", fontSize=8,
    textColor=GRAY_BODY, leading=11,
)
_st_card_link = ParagraphStyle(
    "card_link", fontName="Helvetica-Bold", fontSize=8,
    textColor=CYBER_CYAN_TXT, leading=10,
)


class PrecioBadge(Flowable):
    """Pastilla redondeada con el precio, estilo catálogo digital. Si se
    pasa `link`, la pastilla queda clickeable hacia esa URL."""

    def __init__(self, texto, height=20, padding=10, bg=GAMER_GREEN, color=white, link=None):
        super().__init__()
        self.texto = texto
        self.height = height
        self.padding = padding
        self.bg = bg
        self.color = color
        self.link = link
        self.width = stringWidth(texto, "Helvetica-Bold", 10) + padding * 2

    def wrap(self, availWidth, availHeight):
        return (self.width, self.height)

    def draw(self):
        c = self.canv
        c.setFillColor(self.bg)
        c.roundRect(0, 0, self.width, self.height, radius=self.height / 2, fill=1, stroke=0)
        c.setFillColor(self.color)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(self.width / 2, self.height / 2 - 3.5, self.texto)
        if self.link:
            c.linkURL(self.link, (0, 0, self.width, self.height), relative=1)


def _truncar(texto, maximo=130):
    texto = (texto or "").strip()
    if len(texto) <= maximo:
        return texto
    return texto[:maximo].rsplit(" ", 1)[0] + "…"


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


def _urls_por_modo(imagenes_qs):
    """
    Devuelve TODAS las URLs de las imágenes de una figura, respetando lo
    elegido por imagen en el carrusel (mismo criterio que el carrusel
    público y el de admin): Solo IA, Solo original, o Ambas (aporta 2 URLs).
    Sin límite de cantidad.
    """
    urls = []
    for fi in imagenes_qs:
        url_ia = fi.imagen_procesada.url if fi.imagen_procesada else None
        url_normal = fi.imagen.url if fi.imagen else None
        if fi.modo_carrusel == FiguraImagen.AMBAS:
            urls.extend(u for u in (url_ia, url_normal) if u)
        elif fi.modo_carrusel == FiguraImagen.NORMAL:
            if url_normal:
                urls.append(url_normal)
        else:  # IA (default): usar la IA si existe, si no caer a la normal.
            if url_ia:
                urls.append(url_ia)
            elif url_normal:
                urls.append(url_normal)
    return urls


def _urls_para_pdf(imagenes_qs):
    """Igual que `_urls_por_modo`, pero limitado a 5 imágenes (espacio del collage del PDF)."""
    return _urls_por_modo(imagenes_qs)[:5]


def _bloque_producto(figura, ancho_bloque, base_url=None, cliente_id=None, comision=None):
    """
    Tarjeta de producto estilo catálogo digital: foto a la izquierda,
    nombre + descripción + pastilla de precio a la derecha. Si se pasa
    `base_url`, el nombre y el precio quedan clickeables hacia la ficha
    del producto en la web pública (deep-link ?figura=<id>[&cliente=<id>]).
    Si se pasa `comision`, el precio mostrado se incrementa en ese %.
    """
    ancho_img = ancho_bloque * 0.34
    ancho_txt = ancho_bloque * 0.66

    link = None
    if base_url:
        link = f"{base_url}/?figura={figura.pk}"
        if cliente_id:
            link += f"&cliente={cliente_id}"

    urls = _urls_para_pdf(figura.imagenes.all())
    img_flow = None
    if urls:
        buf, ratio = _descargar_imagen(urls[0])
        if buf:
            ALTURA_MAX = 4 * cm
            ancho_final, alto_final = ancho_img, ancho_img * ratio
            if alto_final > ALTURA_MAX:
                alto_final = ALTURA_MAX
                ancho_final = alto_final / ratio
            img_flow = Image(buf, width=ancho_final, height=alto_final)

    contenido_img = [img_flow] if img_flow else [Spacer(ancho_img, 2.5 * cm)]

    nombre_txt = f'<a href="{link}">{figura.nombre}</a>' if link else figura.nombre
    contenido_txt = [Paragraph(nombre_txt, _st_card_nombre)]
    if figura.descripcion:
        contenido_txt.append(Paragraph(_truncar(figura.descripcion), _st_card_desc))
    if link:
        contenido_txt.append(Paragraph(f'<a href="{link}">Ver en la web →</a>', _st_card_link))
    contenido_txt.append(Spacer(1, 6))

    precio = float(figura.precio_total)
    if comision:
        precio = round(precio * (1 + float(comision) / 100))
    contenido_txt.append(PrecioBadge(f"${precio:,.0f} COP", link=link))

    tabla = Table([[contenido_img, contenido_txt]], colWidths=[ancho_img, ancho_txt])
    tabla.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("ALIGN",        (0, 0), (0, 0), "CENTER"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 8),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return tabla


def _grid_figuras(figuras_lista, ancho_disponible, base_url=None, cliente_id=None, comision=None):
    """Grilla de 2 columnas de tarjetas de producto, como un catálogo digital."""
    gap = 0.7 * cm
    ancho_bloque = (ancho_disponible - gap) / 2

    filas = []
    fila = []
    for figura in figuras_lista:
        fila.append(_bloque_producto(
            figura, ancho_bloque, base_url=base_url,
            cliente_id=cliente_id, comision=comision,
        ))
        if len(fila) == 2:
            filas.append(fila)
            fila = []
    if fila:
        fila.append(Spacer(ancho_bloque, 1))
        filas.append(fila)

    tabla = Table(filas, colWidths=[ancho_bloque, ancho_bloque])
    tabla.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (0, -1), gap),
        ("RIGHTPADDING",  (1, 0), (1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
    ]))
    return tabla


def _agrupar_por_categoria(figuras):
    """
    Agrupa las figuras por categoría, preservando el orden alfabético de
    categoría. Una figura con varias categorías aparece en cada sección
    correspondiente; las sin categoría van al final en "Sin categoría".
    """
    grupos = {}
    orden = []
    sin_categoria = []
    for figura in figuras:
        categorias = list(figura.categorias.all())
        if not categorias:
            sin_categoria.append(figura)
            continue
        for cat in categorias:
            if cat.id not in grupos:
                grupos[cat.id] = (cat, [])
                orden.append(cat.id)
            grupos[cat.id][1].append(figura)

    orden.sort(key=lambda cid: grupos[cid][0].nombre.lower())
    resultado = [grupos[cid] for cid in orden]
    if sin_categoria:
        resultado.append((None, sin_categoria))
    return resultado


def _decorar_pagina(canvas, doc):
    """Callback: pinta fondo rosa claro en cada página y footer de marca."""
    PAGE_W, PAGE_H = A4
    canvas.saveState()
    # Fondo
    canvas.setFillColor(BG_PAGINA)
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


def _generar_pdf(figuras, nombre_empresa, empresa=None, categoria=None, base_url=None,
                  cliente_id=None, comision=None):
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
        fontSize=28, textColor=DEEP_SPACE, alignment=TA_CENTER,
        fontName="Helvetica-Bold", spaceAfter=6, leading=34)
    st_cover_sub = ParagraphStyle("cover_sub", parent=styles["Normal"],
        fontSize=14, textColor=CYBER_CYAN_TXT, alignment=TA_CENTER, spaceAfter=4)
    st_cover_slogan = ParagraphStyle("cover_slogan", parent=styles["Normal"],
        fontSize=11, textColor=VOXEL_MAG_TXT, alignment=TA_CENTER,
        fontName="Helvetica-Oblique", spaceAfter=6)
    st_cover_url = ParagraphStyle("cover_url", parent=styles["Normal"],
        fontSize=10, textColor=GAMER_GREEN, alignment=TA_CENTER,
        fontName="Helvetica-Bold")
    st_badge = ParagraphStyle("badge", parent=styles["Normal"],
        fontSize=8, textColor=GRAY_BODY, alignment=TA_CENTER, spaceAfter=4)
    st_categoria = ParagraphStyle("categoria", parent=styles["Heading1"],
        fontSize=18, textColor=VOXEL_MAG_TXT, alignment=TA_LEFT,
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

    # ── FIGURAS: grilla de 2 columnas estilo catálogo digital ──────────────────
    if categoria:
        # Ya filtrado a una sola categoría: sin secciones, grilla plana.
        story.append(_grid_figuras(list(figuras), ancho, base_url=base_url, cliente_id=cliente_id, comision=comision))
    else:
        # Sin filtro: agrupar en secciones por categoría (una figura con
        # varias categorías aparece repetida en cada sección que le aplica).
        for cat, figuras_cat in _agrupar_por_categoria(figuras):
            nombre_categoria = cat.nombre if cat else "Sin categoría"
            story.append(Paragraph(nombre_categoria.upper(), st_categoria))
            story.append(HRFlowable(width=ancho, color=CYBER_CYAN, thickness=1, spaceAfter=8))
            story.append(_grid_figuras(figuras_cat, ancho, base_url=base_url, cliente_id=cliente_id, comision=comision))
            story.append(Spacer(1, 0.4 * cm))

    doc.build(story, onFirstPage=_decorar_pagina, onLaterPages=_decorar_pagina)
    buf.seek(0)
    return buf


def _qs_y_empresa(request):
    from apps.produccion.models.empresa import Empresa
    from apps.produccion.models.figura import CategoriaFigura

    perfil = getattr(request.user, "perfil", None)
    qs = (
        Figura.objects
        .prefetch_related("imagenes", "categorias", "figura_piezas__pieza")
        .order_by("nombre")
    )

    categoria = None
    categoria_id = request.GET.get("categorias__id__exact")
    if categoria_id:
        qs = qs.filter(categorias__id=categoria_id).distinct()
        categoria = CategoriaFigura.objects.filter(pk=categoria_id).first()

    if perfil and perfil.empresa_id:
        return qs.filter(empresa=perfil.empresa), str(perfil.empresa), perfil.empresa, categoria
    # Superadmin sin perfil: usar la primera empresa disponible para el logo
    empresa = Empresa.objects.filter(logo__isnull=False).exclude(logo="").first() \
              or Empresa.objects.first()
    nombre = str(empresa) if empresa else "Todas las empresas"
    return qs, nombre, empresa, categoria


def _responder_pdf_catalogo(request):
    from apps.produccion.models import Cliente

    figuras, nombre_empresa, empresa, categoria = _qs_y_empresa(request)
    base_url = request.build_absolute_uri("/").rstrip("/")

    cliente_id = request.GET.get("cliente")
    comision = None
    if cliente_id:
        cliente = Cliente.objects.filter(pk=cliente_id).only("comision").first()
        if cliente:
            comision = cliente.comision
        else:
            cliente_id = None

    buf = _generar_pdf(
        figuras, nombre_empresa, empresa=empresa, categoria=categoria, base_url=base_url,
        cliente_id=cliente_id, comision=comision,
    )
    response = HttpResponse(buf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="catalogo_figuras.pdf"'
    return response


@staff_member_required
def exportar_catalogo_pdf(request):
    """PDF del catálogo (uso interno/admin), usando en cada figura las imágenes
    elegidas en su carrusel. Cada producto enlaza a su ficha en el catálogo
    público (dominio raíz)."""
    return _responder_pdf_catalogo(request)


def exportar_catalogo_pdf_publico(request):
    """Mismo PDF, pero accesible sin sesión — para el botón de descarga del
    catálogo público en el dominio raíz. No expone costo ni piezas (el PDF
    solo muestra nombre, descripción, imagen y precio total)."""
    return _responder_pdf_catalogo(request)
