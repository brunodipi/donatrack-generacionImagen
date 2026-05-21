import io
import math
import textwrap
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont, ImageFilter

app = FastAPI(title="Generador de Medallas DonaTrack")

@app.get("/generar-medalla")
def generar_medalla(
    user: str = Query(...), 
    badge: str = Query(...), 
    descripcion: str = Query("")
):
    ANCHO, ALTO = 1000, 1000
    
    # Paleta de colores
    COLOR_FONDO = "#F9F7F1"
    COLOR_ORO_EXTERIOR = "#DCA828"
    COLOR_ORO_INTERIOR = "#C79A22"
    COLOR_ROJO = "#A6192E"
    COLOR_ROJO_OSCURO = "#7A0016"
    COLOR_CENTRO = "#FFFDF9"
    COLOR_TEXTO = "#2C2C2C"

    # Capa base (JPEG) y capa transparente para las sombras reales
    image = Image.new("RGB", (ANCHO, ALTO), COLOR_FONDO)
    capa_sombras = Image.new("RGBA", (ANCHO, ALTO), (255, 255, 255, 0))
    
    draw = ImageDraw.Draw(image)
    draw_sombras = ImageDraw.Draw(capa_sombras)
    
    centro_x, centro_y = ANCHO // 2, ALTO // 2 - 30 

    # --- 1. DIBUJAR LA ESTRELLA DENTADA Y SOMBRAS ---
    puntos_estrella = []
    num_puntas = 24
    radio_externo = 400
    radio_interno = 340
    
    for i in range(num_puntas * 2):
        angulo = i * math.pi / num_puntas - (math.pi / 2)
        r = radio_externo if i % 2 == 0 else radio_interno
        x = centro_x + r * math.cos(angulo)
        y = centro_y + r * math.sin(angulo)
        puntos_estrella.append((x, y))

    # Sombras de la estrella y el listón (en la capa transparente)
    banner_y = centro_y + 240
    banner_w, banner_h = 600, 110
    
    puntos_sombra_estrella = [(x+8, y+12) for x, y in puntos_estrella]
    draw_sombras.polygon(puntos_sombra_estrella, fill=(0, 0, 0, 70))
    draw_sombras.rectangle([centro_x - banner_w//2 + 8, banner_y + 12, centro_x + banner_w//2 + 8, banner_y + banner_h + 12], fill=(0, 0, 0, 70))

    # Difuminar las sombras y pegarlas en el fondo
    capa_sombras = capa_sombras.filter(ImageFilter.GaussianBlur(8))
    image.paste(capa_sombras, (0, 0), capa_sombras)

    # Estrella dorada principal
    draw.polygon(puntos_estrella, fill=COLOR_ORO_EXTERIOR, outline=COLOR_ORO_INTERIOR, width=5)

    # --- 2. ANILLOS INTERNOS ---
    r_rojo = 310
    draw.ellipse((centro_x - r_rojo, centro_y - r_rojo, centro_x + r_rojo, centro_y + r_rojo), 
                 fill=COLOR_ROJO, outline="#8C1325", width=4)
    
    r_centro = 260
    draw.ellipse((centro_x - r_centro, centro_y - r_centro, centro_x + r_centro, centro_y + r_centro), 
                 fill=COLOR_CENTRO)
    
    r_borde = 255
    draw.ellipse((centro_x - r_borde, centro_y - r_borde, centro_x + r_borde, centro_y + r_borde), 
                 outline=COLOR_ORO_EXTERIOR, width=3)

    # --- 3. FUENTES ---
    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
        font_badge = ImageFont.truetype("DejaVuSans-Bold.ttf", 38) # Reducido un poco para que encaje
        font_desc = ImageFont.truetype("DejaVuSans.ttf", 32)
        font_user = ImageFont.truetype("DejaVuSans-Bold.ttf", 45)
    except IOError:
        font_title = font_badge = font_desc = font_user = ImageFont.load_default()

    # --- 4. TEXTOS PERFECTAMENTE CENTRADOS (anchor="mm") ---
    # Título superior
    draw.text((centro_x, centro_y - 190), "DONA TRACK", font=font_title, fill="#888888", anchor="mm")

    # Nombre de la Insignia (Envuelta a 18 caracteres por si es muy larga)
    lineas_badge = textwrap.wrap(badge.upper(), width=18)
    y_badge = centro_y - 120
    for linea in lineas_badge:
        draw.text((centro_x, y_badge), linea, font=font_badge, fill=COLOR_ROJO, anchor="mm")
        y_badge += 42

    # Línea decorativa dorada
    draw.line((centro_x - 80, centro_y - 45, centro_x + 80, centro_y - 45), fill=COLOR_ORO_EXTERIOR, width=3)

    # Descripción (Envuelta estrictamente a 22 caracteres para no tocar los bordes)
    if descripcion:
        lineas_desc = textwrap.wrap(descripcion, width=22) 
        y_desc = centro_y + 15
        for linea in lineas_desc:
            draw.text((centro_x, y_desc), linea, font=font_desc, fill=COLOR_TEXTO, anchor="mm")
            y_desc += 40

    # --- 5. EL LISTÓN INFERIOR ---
    # "Colas" rojas del listón dobladas hacia atrás
    draw.polygon([(centro_x - 280, banner_y + 50), (centro_x - 400, banner_y + 160), (centro_x - 180, banner_y + 160)], fill=COLOR_ROJO_OSCURO)
    draw.polygon([(centro_x + 280, banner_y + 50), (centro_x + 400, banner_y + 160), (centro_x + 180, banner_y + 160)], fill=COLOR_ROJO_OSCURO)
    
    # Listón dorado frontal
    draw.rectangle([centro_x - banner_w//2, banner_y, centro_x + banner_w//2, banner_y + banner_h], fill=COLOR_ORO_EXTERIOR, outline=COLOR_ORO_INTERIOR, width=3)
    
    # Nombre del Usuario en el centro exacto del listón dorado
    draw.text((centro_x, banner_y + banner_h // 2), user.upper(), font=font_user, fill=COLOR_TEXTO, anchor="mm")

    # --- 6. EXPORTAR ---
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=95)
    buffer.seek(0)
    
    return StreamingResponse(buffer, media_type="image/jpeg")