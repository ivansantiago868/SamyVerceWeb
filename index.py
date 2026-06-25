import os
import glob
from fpdf import FPDF

# Intentar encontrar la imagen del logo automáticamente
image_files = glob.glob("*.jpg") + glob.glob("*.png") + glob.glob("*.jpeg")
logo_path = image_files[0] if image_files else None

class BrandManualPDF(FPDF):
    def header(self):
        # Header simple en páginas internas
        if self.page_no() > 1:
            self.set_font('Arial', 'B', 12)
            self.set_text_color(26, 26, 46)  # Dark Blue
            self.cell(0, 10, 'SamyVerse - Manual de Marca & Digital', 0, 1, 'R')
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Pagina {self.page_no()} | www.samyverse3d.com', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(213, 0, 249) # Magenta Neon
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 6, body)
        self.ln()
    
    def sub_chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(26, 26, 46)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)

    def color_swatch(self, r, g, b, name, hex_code, usage):
        self.set_fill_color(r, g, b)
        self.rect(self.get_x(), self.get_y(), 25, 25, 'F')
        self.set_xy(self.get_x() + 30, self.get_y())
        self.set_font('Arial', 'B', 11)
        self.cell(0, 6, name, 0, 1)
        self.set_xy(self.get_x() + 30, self.get_y())
        self.set_font('Courier', '', 10)
        self.cell(0, 6, f"HEX: {hex_code}", 0, 1)
        self.set_xy(self.get_x() + 30, self.get_y())
        self.set_font('Arial', '', 9)
        self.multi_cell(0, 5, f"Uso: {usage}")
        self.ln(15)

# Crear PDF
pdf = BrandManualPDF()
pdf.set_auto_page_break(auto=True, margin=15)

# --- PORTADA ---
pdf.add_page()
pdf.set_fill_color(26, 26, 46) # Fondo oscuro
pdf.rect(0, 0, 210, 297, 'F')

# Logo en portada
if logo_path:
    try:
        pdf.image(logo_path, x=30, y=60, w=150)
    except:
        pass # Si falla, solo muestra texto

pdf.set_y(210)
pdf.set_font('Arial', 'B', 30)
pdf.set_text_color(255, 255, 255)
pdf.cell(0, 10, 'MANUAL DE MARCA', 0, 1, 'C')
pdf.set_font('Arial', '', 14)
pdf.set_text_color(0, 229, 255) # Cyan Neon
pdf.cell(0, 10, 'Identidad Visual & Digital', 0, 1, 'C')
pdf.ln(5)
pdf.set_font('Courier', 'B', 12)
pdf.set_text_color(255, 255, 255)
pdf.cell(0, 10, 'www.samyverse3d.com', 0, 1, 'C')

# --- PAGINA 2: ESENCIA ---
pdf.add_page()
pdf.chapter_title("1. LA ESENCIA")
text_intro = (
    "Nombre: SamyVerse\n"
    "Slogan: UN UNIVERSO DE SORPRESAS\n"
    "Dominio Oficial: samyverse3d.com\n\n"
    "Concepto:\n"
    "SamyVerse es el portal donde la imaginación digital aterriza en la realidad. "
    "Fusionamos la estética gamer y espacial para crear juguetes impresos en 3D únicos.\n\n"
    "Público: Niños (4-12 años) exploradores, gamers y creativos."
)
pdf.chapter_body(text_intro)

# --- PAGINA 3: COLORES ---
pdf.add_page()
pdf.chapter_title("2. PALETA DE COLORES (NEON VOXEL)")
pdf.chapter_body("Colores extraídos del logo oficial para uso web e impreso.")
pdf.color_swatch(0, 229, 255, "Cyber Cyan", "#00E5FF", "Títulos web, bordes activos, tecnología.")
pdf.color_swatch(213, 0, 249, "Voxel Magenta", "#D500F9", "Acentos vibrantes, magia, degradados.")
pdf.color_swatch(0, 255, 157, "Gamer Green", "#00FF9D", "Botones de COMPRA, llamadas a la acción.")
pdf.color_swatch(26, 26, 46, "Deep Space Blue", "#1A1A2E", "Fondo de la página web (Body Background).")

# --- PAGINA 4: TIPOGRAFÍA ---
pdf.add_page()
pdf.chapter_title("3. TIPOGRAFÍA")
text_typo = (
    "A. Fuente Principal (Web Headings): ORBITRON\n"
    "Uso: Títulos de secciones en la web, banners promocionales.\n\n"
    "B. Fuente de Lectura (Web Body): MONTSERRAT\n"
    "Uso: Descripciones de productos en WooCommerce, menús de navegación."
)
pdf.chapter_body(text_typo)

# --- PAGINA 5: ECOSISTEMA DIGITAL (NUEVA SECCIÓN) ---
pdf.add_page()
pdf.chapter_title("4. ECOSISTEMA DIGITAL")
pdf.chapter_body("Lineamientos técnicos y visuales para la presencia online de la marca.")

pdf.sub_chapter_title("A. Dominio y Alojamiento")
text_digital = (
    "URL Oficial: https://www.samyverse3d.com\n"
    "Proveedor de Hosting: Hostinger\n"
    "Plataforma Base: WordPress + WooCommerce\n"
)
pdf.chapter_body(text_digital)

pdf.sub_chapter_title("B. Estilo Web (UI Kit)")
text_ui = (
    "- Fondo General: Deep Space Blue (#1A1A2E). Evitar fondos blancos puros para no perder el efecto 'Gamer'.\n"
    "- Botones (CTA): Deben ser siempre 'Gamer Green' (#00FF9D) con texto oscuro para máximo contraste.\n"
    "- Tarjetas de Producto: Fondo semi-oscuro (#252540) con bordes delgados neón (Magenta o Cyan) que brillan al pasar el mouse (Hover effect)."
)
pdf.chapter_body(text_ui)

# --- PAGINA 6: TONO Y GRAFICOS ---
pdf.add_page()
pdf.chapter_title("5. ELEMENTOS GRÁFICOS & TONO")
text_tone = (
    "- Vóxeles y Píxeles 3D: Usar patrones de cubos en los banners web.\n"
    "- Tono de Voz: '¡Bienvenido a la misión!', 'Despegando envío', 'Objeto identificado'.\n"
    "- Fotografía: Productos iluminados con luces led de colores (RGB) para resaltar el volumen 3D."
)
pdf.chapter_body(text_tone)

pdf_output_path = "Manual_Marca_SamyVerse_Digital.pdf"
pdf.output(pdf_output_path)

pdf_output_path