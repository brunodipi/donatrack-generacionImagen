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
    
    # Paleta de colores más rica y viva (basada en tu referencia)
    COLOR_FONDO = "#F9F7F1"        # Beige muy clarito
    COLOR_ORO_EXTERIOR = "#DCA828" # Oro vivo
    COLOR_ORO_INTERIOR = "#C79A22" # Oro sombra para el borde
    COLOR_ROJO = "#A6192E"         # Rojo profundo
    COLOR_ROJO_OSCURO = "#7A0016"  # Sombra del listón
    COLOR_CENTRO = "#FFFDF9"       # Blanco cálido
    COLOR_TEXTO = "#2C2C2C"        # Casi negro para buena lectura

    # 1. Crear imagen base y capas para sombras
    image = Image.new("RGB", (ANCHO, ALTO), COLOR_FONDO)
    capa_sombras = Image.new("RGBA", (ANCHO, ALTO), (255, 255, 255, 0))
    
    draw = ImageDraw.Draw(image)
    draw_sombras = ImageDraw.Draw(capa_sombras)
    
    # Subimos un poquito el centro para dejar espacio al listón de abajo
    centro_x, centro_y = ANCHO // 2, ALTO // 2 - 30 

    # --- 2. DIBUJAR LA ESTRELLA DENTADA (Fondo dorado) ---
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

    # Sombra difuminada de la estrella
    puntos_sombra = [(x+10, y+15) for x, y in puntos_estrella]
    draw_sombras.polygon(puntos_sombra, fill=(0, 0, 0, 60))
    capa_sombras = capa_sombras.filter(ImageFilter.GaussianBlur(8)) # Magia del volumen 3D
    image.paste(capa_sombras, (0, 0), capa_sombras)

    # Estrella dorada principal
    draw.polygon(puntos_estrella, fill=COLOR_ORO_EXTERIOR, outline=COLOR_ORO_INTERIOR, width=5)

    # --- 3. ANILLOS INTERNOS ---
    # Anillo Rojo grueso
    r_rojo = 310
    draw.ellipse((centro_x - r_rojo, centro_y - r_rojo, centro_x + r_rojo, centro_y + r_rojo), 
                 fill=COLOR_ROJO, outline="#8C1325", width=4)
    
    # Círculo Blanco/Crema central
    r_centro = 260
    draw.ellipse((centro_x - r_centro, centro_y - r_centro, centro_x + r_centro, centro_y + r_centro), 
                 fill=COLOR_CENTRO)
    
    # Borde dorado sutil interno
    r_borde = 255
    draw.ellipse((centro_x - r_borde, centro_y - r_borde, centro_x + r_borde, centro_y + r_borde), 
                 outline=COLOR_ORO_EXTERIOR, width=3)

    # --- 4. FUENTES ---
    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
        font_badge = ImageFont.truetype("DejaVuSans-Bold.ttf", 45)
        font_desc = ImageFont.truetype("DejaVuSans.ttf", 32)
        font_user = ImageFont.truetype("DejaVuSans-Bold.ttf", 45)
    except IOError:
        font_title = font_badge = font_desc = font_user = ImageFont.load_default()

    # --- 5. TEXTOS DEL CENTRO ---
    # Marca superior
    txt_top = "DONA TRACK"
    bbox_top = draw.textbbox((0, 0), txt_top, font=font_title)
    draw.text((centro_x - (bbox_top[2]-bbox_top[0])//2, centro_y - 190), txt_top, font=font_title, fill="#888888")

    # Nombre de la Medalla (Grande y Rojo)
    bbox_badge = draw.textbbox((0, 0), badge.upper(), font=font_badge)
    draw.text((centro_x - (bbox_badge[2]-bbox_badge[0])//2, centro_y - 120), badge.upper(), font=font_badge, fill=COLOR_ROJO)

    # Línea decorativa
    draw.line((centro_x - 80, centro_y - 40, centro_x + 80, centro_y - 40), fill=COLOR_ORO_EXTERIOR, width=3)

    # La Descripción (Cortada inteligentemente en renglones)
    if descripcion:
        lineas = textwrap.wrap(descripcion, width=30) # Corta a los 30 caracteres
        y_text = centro_y + 10
        for linea in lineas:
            bbox_line = draw.textbbox((0, 0), linea, font=font_desc)
            w_line = bbox_line[2] - bbox_line[0]
            draw.text((centro_x - w_line//2, y_text), linea, font=font_desc, fill=COLOR_TEXTO)
            y_text += 45

    # --- 6. EL LISTÓN INFERIOR (Banner) ---
    banner_y = centro_y + 240
    banner_w, banner_h = 600, 110
    
    # "Colas" rojas del listón dobladas hacia atrás
    draw.polygon([(centro_x - 280, banner_y + 50), (centro_x - 400, banner_y + 160), (centro_x - 180, banner_y + 160)], fill=COLOR_ROJO_OSCURO)
    draw.polygon([(centro_x + 280, banner_y + 50), (centro_x + 400, banner_y + 160), (centro_x + 180, banner_y + 160)], fill=COLOR_ROJO_OSCURO)
    
    # Sombra del listón dorado
    draw.rectangle([centro_x - banner_w//2 + 10, banner_y + 15, centro_x + banner_w//2 + 10, banner_y + banner_h + 15], fill="#00000030")

    # Listón dorado frontal
    draw.rectangle([centro_x - banner_w//2, banner_y, centro_x + banner_w//2, banner_y + banner_h], fill=COLOR_ORO_EXTERIOR, outline=COLOR_ORO_INTERIOR, width=3)
    
    # Nombre del Usuario en el listón
    bbox_user = draw.textbbox((0, 0), user.upper(), font=font_user)
    draw.text((centro_x - (bbox_user[2]-bbox_user[0])//2, banner_y + (banner_h - (bbox_user[3]-bbox_user[1]))//2 - 5), user.upper(), font=font_user, fill=COLOR_TEXTO)

    # --- 7. EXPORTAR ---
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=95)
    buffer.seek(0)
    
    return StreamingResponse(buffer, media_type="image/jpeg")