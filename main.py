import io
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont

app = FastAPI(title="Generador de Medallas DonaTrack")

@app.get("/generar-medalla")
def generar_medalla(user: str = Query(...), badge: str = Query(...)):
    ANCHO, ALTO = 1000, 1000
    COLOR_ORO_BASE = "#D4AF37"
    COLOR_ORO_BRILLO = "#FDD017"
    COLOR_ORO_SOMBRA = "#996515"
    COLOR_TEXTO_INSIGNIA = "#3A3A3A"

    # Lienzo transparente
    image = Image.new("RGB", (ANCHO, ALTO), "#FAF8F5")
    draw = ImageDraw.Draw(image)
    centro_x, centro_y = ANCHO // 2, ALTO // 2

    # Fuentes estándar que los servidores Linux tienen por defecto
    try:
        font_badge = ImageFont.truetype("DejaVuSans.ttf", 60)
        font_user = ImageFont.truetype("DejaVuSans-Bold.ttf", 70)
    except IOError:
        font_badge = ImageFont.load_default()
        font_user = ImageFont.load_default()

    # --- Lógica de Dibujo (Tu mismo diseño) ---
    radio_base = 400
    draw.ellipse((centro_x - radio_base + 10, centro_y - radio_base + 15, 
                  centro_x + radio_base + 10, centro_y + radio_base + 15), fill="#00000030")
    draw.ellipse((centro_x - radio_base, centro_y - radio_base, 
                  centro_x + radio_base, centro_y + radio_base), fill=COLOR_ORO_BASE, outline=COLOR_ORO_SOMBRA, width=3)

    radio_interno = radio_base - 30
    draw.ellipse((centro_x - radio_interno, centro_y - radio_interno, 
                  centro_x + radio_interno, centro_y + radio_interno), fill=COLOR_ORO_BRILLO, outline=COLOR_ORO_SOMBRA, width=5)

    # Título superior
    texto_titulo = "DONA TRACK"
    bbox_titulo = draw.textbbox((0, 0), texto_titulo, font=font_badge)
    w_t = bbox_titulo[2] - bbox_titulo[0]
    draw.text((centro_x - w_t//2 + 3, centro_y - radio_base + 120 + 3), texto_titulo, font=font_badge, fill=COLOR_ORO_SOMBRA)
    draw.text((centro_x - w_t//2, centro_y - radio_base + 120), texto_titulo, font=font_badge, fill=COLOR_TEXTO_INSIGNIA)

    # Banner inferior
    banner_w, banner_h = 750, 150
    banner_y = centro_y + 150
    puntos_banner = [
        (centro_x - banner_w//2, banner_y), (centro_x + banner_w//2, banner_y),
        (centro_x + banner_w//2 - 50, banner_y + banner_h), (centro_x - banner_w//2 + 50, banner_y + banner_h)
    ]
    draw.polygon([(x+8, y+8) for x,y in puntos_banner], fill="#00000030")
    draw.polygon(puntos_banner, fill=COLOR_ORO_BASE, outline=COLOR_ORO_SOMBRA, width=4)

    # Texto del Usuario
    bbox_user = draw.textbbox((0, 0), user.upper(), font=font_user)
    w_u = bbox_user[2] - bbox_user[0]
    h_u = bbox_user[3] - bbox_user[1]
    pos_y_user = banner_y + (banner_h - h_u) // 2 - 10
    draw.text((centro_x - w_u//2 + 4, pos_y_user + 4), user.upper(), font=font_user, fill=COLOR_ORO_SOMBRA)
    draw.text((centro_x - w_u//2 - 2, pos_y_user - 2), user.upper(), font=font_user, fill=COLOR_ORO_BRILLO)
    draw.text((centro_x - w_u//2, pos_y_user), user.upper(), font=font_user, fill=COLOR_TEXTO_INSIGNIA)

    # Texto de la insignia
    bbox_badge = draw.textbbox((0, 0), badge, font=font_badge)
    w_b = bbox_badge[2] - bbox_badge[0]
    h_b = bbox_badge[3] - bbox_badge[1]
    draw.text((centro_x - w_b//2 + 2, centro_y - h_b//2 + 10 + 2), badge, font=font_badge, fill=COLOR_ORO_SOMBRA)
    draw.text((centro_x - w_b//2, centro_y - h_b//2 + 10), badge, font=font_badge, fill=COLOR_TEXTO_INSIGNIA)

    # En lugar de guardar en disco, enviamos el archivo binario directamente por la red
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=95)
    buffer.seek(0)
    
    return StreamingResponse(buffer, media_type="image/jpeg")