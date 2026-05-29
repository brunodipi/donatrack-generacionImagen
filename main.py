import io
import math
import textwrap
from typing import List
from pydantic import BaseModel
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont, ImageFilter

app = FastAPI(title="Generador de Medallas DonaTrack")

# --- MODELO DE DATOS PARA EL POST ---
class DonanteRanking(BaseModel):
    Mes: str
    Donante: str
    CantidadMisiones: int

# --- RUTA 1: LA MEDALLA INDIVIDUAL (GET) ---
@app.get("/generar-medalla")
def generar_medalla(
    user: str = Query(...), 
    badge: str = Query(...), 
    descripcion: str = Query("")
):
    ANCHO, ALTO = 1000, 1000
    COLOR_FONDO = "#F9F7F1"
    COLOR_ORO_EXTERIOR = "#DCA828"
    COLOR_ORO_INTERIOR = "#C79A22"
    COLOR_ROJO = "#A6192E"
    COLOR_ROJO_OSCURO = "#7A0016"
    COLOR_CENTRO = "#FFFDF9"
    COLOR_TEXTO = "#2C2C2C"

    image = Image.new("RGB", (ANCHO, ALTO), COLOR_FONDO)
    capa_sombras = Image.new("RGBA", (ANCHO, ALTO), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw_sombras = ImageDraw.Draw(capa_sombras)
    centro_x, centro_y = ANCHO // 2, ALTO // 2 - 30 

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

    banner_y = centro_y + 240
    banner_w, banner_h = 600, 110
    
    puntos_sombra_estrella = [(x+8, y+12) for x, y in puntos_estrella]
    draw_sombras.polygon(puntos_sombra_estrella, fill=(0, 0, 0, 70))
    draw_sombras.rectangle([centro_x - banner_w//2 + 8, banner_y + 12, centro_x + banner_w//2 + 8, banner_y + banner_h + 12], fill=(0, 0, 0, 70))
    capa_sombras = capa_sombras.filter(ImageFilter.GaussianBlur(8))
    image.paste(capa_sombras, (0, 0), capa_sombras)

    draw.polygon(puntos_estrella, fill=COLOR_ORO_EXTERIOR, outline=COLOR_ORO_INTERIOR, width=5)

    r_rojo = 310
    draw.ellipse((centro_x - r_rojo, centro_y - r_rojo, centro_x + r_rojo, centro_y + r_rojo), fill=COLOR_ROJO, outline="#8C1325", width=4)
    r_centro = 260
    draw.ellipse((centro_x - r_centro, centro_y - r_centro, centro_x + r_centro, centro_y + r_centro), fill=COLOR_CENTRO)
    r_borde = 255
    draw.ellipse((centro_x - r_borde, centro_y - r_borde, centro_x + r_borde, centro_y + r_borde), outline=COLOR_ORO_EXTERIOR, width=3)

    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
        font_badge = ImageFont.truetype("DejaVuSans-Bold.ttf", 38)
        font_desc = ImageFont.truetype("DejaVuSans.ttf", 32)
        font_user = ImageFont.truetype("DejaVuSans-Bold.ttf", 45)
    except IOError:
        font_title = font_badge = font_desc = font_user = ImageFont.load_default()

    draw.text((centro_x, centro_y - 190), "DONA TRACK", font=font_title, fill="#888888", anchor="mm")
    lineas_badge = textwrap.wrap(badge.upper(), width=18)
    y_badge = centro_y - 120
    for linea in lineas_badge:
        draw.text((centro_x, y_badge), linea, font=font_badge, fill=COLOR_ROJO, anchor="mm")
        y_badge += 42

    draw.line((centro_x - 80, centro_y - 45, centro_x + 80, centro_y - 45), fill=COLOR_ORO_EXTERIOR, width=3)

    if descripcion:
        lineas_desc = textwrap.wrap(descripcion, width=22) 
        y_desc = centro_y + 15
        for linea in lineas_desc:
            draw.text((centro_x, y_desc), linea, font=font_desc, fill=COLOR_TEXTO, anchor="mm")
            y_desc += 40

    draw.polygon([(centro_x - 280, banner_y + 50), (centro_x - 400, banner_y + 160), (centro_x - 180, banner_y + 160)], fill=COLOR_ROJO_OSCURO)
    draw.polygon([(centro_x + 280, banner_y + 50), (centro_x + 400, banner_y + 160), (centro_x + 180, banner_y + 160)], fill=COLOR_ROJO_OSCURO)
    draw.rectangle([centro_x - banner_w//2, banner_y, centro_x + banner_w//2, banner_y + banner_h], fill=COLOR_ORO_EXTERIOR, outline=COLOR_ORO_INTERIOR, width=3)
    draw.text((centro_x, banner_y + banner_h // 2), user.upper(), font=font_user, fill=COLOR_TEXTO, anchor="mm")

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=95)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/jpeg")


# --- RUTA 2: EL TOP 3 MENSUAL (POST) ---
@app.post("/generar-top3")
def generar_top3(donantes: List[DonanteRanking]):
    ANCHO, ALTO = 1080, 1080 
    COLOR_FONDO = "#F9F7F1"
    COLOR_ORO = "#DCA828"
    COLOR_PLATA = "#C0C0C0"
    COLOR_BRONCE = "#CD7F32"
    COLOR_ROJO = "#A6192E"
    COLOR_TEXTO = "#2C2C2C"

    image = Image.new("RGB", (ANCHO, ALTO), COLOR_FONDO)
    draw = ImageDraw.Draw(image)
    
    try:
        font_titulo = ImageFont.truetype("DejaVuSans-Bold.ttf", 60)
        font_mes = ImageFont.truetype("DejaVuSans.ttf", 40)
        font_nombre = ImageFont.truetype("DejaVuSans-Bold.ttf", 45)
        font_puntos = ImageFont.truetype("DejaVuSans.ttf", 35)
        font_podio = ImageFont.truetype("DejaVuSans-Bold.ttf", 120)
    except:
        font_titulo = font_mes = font_nombre = font_puntos = font_podio = ImageFont.load_default()

    # Títulos
    mes_nombre = donantes[0].Mes if donantes else "Mes"
    draw.text((ANCHO//2, 120), "TOP DONANTES", font=font_titulo, fill=COLOR_ROJO, anchor="mm")
    draw.text((ANCHO//2, 190), f"Ranking Mensual - {mes_nombre}", font=font_mes, fill="#888888", anchor="mm")

    # --- LÓGICA DINÁMICA DE POSICIONAMIENTO ---
    cantidad = len(donantes)
    config = []

    if cantidad == 1:
        # Solo el 1ro, centrado y más imponente
        config = [{"idx": 0, "x": 540, "h": 500, "w": 400, "color": COLOR_ORO, "label": "1"}]
    elif cantidad == 2:
        # El 1ro y 2do centrados como pareja (evita el hueco del 3ro)
        config = [
            {"idx": 0, "x": 690, "h": 450, "w": 280, "color": COLOR_ORO, "label": "1"},
            {"idx": 1, "x": 390, "h": 320, "w": 280, "color": COLOR_PLATA, "label": "2"}
        ]
    else:
        # El Top 3 completo clásico
        config = [
            {"idx": 0, "x": 540, "h": 450, "w": 280, "color": COLOR_ORO, "label": "1"},
            {"idx": 1, "x": 240, "h": 320, "w": 280, "color": COLOR_PLATA, "label": "2"},
            {"idx": 2, "x": 840, "h": 220, "w": 280, "color": COLOR_BRONCE, "label": "3"}
        ]

    for c in config:
        if c["idx"] < len(donantes):
            d = donantes[c["idx"]]
            x, h, w = c["x"], c["h"], c["w"]
            
            # Dibujar Bloque del Podio con ancho dinámico
            draw.rectangle([x - w//2, 900-h, x + w//2, 900], fill=c["color"], outline=COLOR_TEXTO, width=3)
            # Número de posición decorativo
            draw.text((x, 900 - h//2), c["label"], font=font_podio, fill="#FFFFFF55", anchor="mm")
            # Nombre y misiones
            draw.text((x, 900 - h - 80), d.Donante.upper(), font=font_nombre, fill=COLOR_TEXTO, anchor="mm")
            draw.text((x, 900 - h - 35), f"{d.CantidadMisiones} misiones", font=font_puntos, fill="#555555", anchor="mm")

    # Pie de página institucional
    draw.rectangle([0, 950, ANCHO, 1080], fill=COLOR_ROJO)
    draw.text((ANCHO//2, 1015), "DONA TRACK - CONSTRUYENDO FUTURO", font=font_mes, fill="#FFFFFF", anchor="mm")

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=95)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/jpeg")