"""
Genera QR en estilo estampilla postal para Il Postino Bot.
"""

import io
import base64


def generar_qr_estampilla(url: str, nombre: str = "") -> bytes:
    """Genera un QR con estética de estampilla postal y devuelve los bytes PNG.

    Args:
        url: URL del sitio a codificar.
        nombre: Nombre del usuario para la etiqueta de la estampilla.

    Returns:
        bytes del PNG generado.
    """
    import qrcode
    from PIL import Image, ImageDraw, ImageFont

    # Generar QR
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="#2D2926", back_color="#FDFBF7")
    qr_img = qr_img.convert("RGB")
    qr_size = qr_img.size[0]

    # Canvas de la estampilla: más ancho y alto que el QR
    stamp_w = qr_size + 60
    stamp_h = qr_size + 110
    stamp = Image.new("RGB", (stamp_w, stamp_h), "#FDFBF7")
    draw = ImageDraw.Draw(stamp)

    # Marco serrado de estampilla (rectángulo con esquinas decoradas)
    margin = 12
    draw.rectangle(
        [margin, margin, stamp_w - margin, stamp_h - margin],
        outline="#A0522D",
        width=3,
    )
    # Puntitos en los bordes (simulan el picado de la estampilla)
    dot_r = 5
    dot_spacing = 20
    for x in range(margin + dot_spacing, stamp_w - margin, dot_spacing):
        draw.ellipse([x - dot_r, margin - dot_r, x + dot_r, margin + dot_r],
                     fill="#FDFBF7", outline="#A0522D", width=2)
        draw.ellipse([x - dot_r, stamp_h - margin - dot_r,
                      x + dot_r, stamp_h - margin + dot_r],
                     fill="#FDFBF7", outline="#A0522D", width=2)
    for y in range(margin + dot_spacing, stamp_h - margin, dot_spacing):
        draw.ellipse([margin - dot_r, y - dot_r, margin + dot_r, y + dot_r],
                     fill="#FDFBF7", outline="#A0522D", width=2)
        draw.ellipse([stamp_w - margin - dot_r, y - dot_r,
                      stamp_w - margin + dot_r, y + dot_r],
                     fill="#FDFBF7", outline="#A0522D", width=2)

    # Título arriba
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 16)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", 12)
    except Exception:
        font_title = ImageFont.load_default()
        font_small = font_title

    title_text = "IL POSTINO"
    title_bbox = draw.textbbox((0, 0), title_text, font=font_title)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((stamp_w - title_w) // 2, 22), title_text, fill="#A0522D", font=font_title)

    # QR centrado
    qr_x = (stamp_w - qr_size) // 2
    qr_y = 48
    stamp.paste(qr_img, (qr_x, qr_y))

    # Nombre abajo
    if nombre:
        nombre_short = nombre[:22]
        nombre_bbox = draw.textbbox((0, 0), nombre_short, font=font_small)
        nombre_w = nombre_bbox[2] - nombre_bbox[0]
        draw.text(((stamp_w - nombre_w) // 2, qr_y + qr_size + 10),
                  nombre_short, fill="#7a6f68", font=font_small)

    # "Tu carta al mundo" abajo
    tag_text = "✉ carta digital enviada al mundo"
    try:
        tag_bbox = draw.textbbox((0, 0), tag_text, font=font_small)
        tag_w = tag_bbox[2] - tag_bbox[0]
        draw.text(((stamp_w - tag_w) // 2, stamp_h - 28),
                  tag_text, fill="#A0522D", font=font_small)
    except Exception:
        pass

    buf = io.BytesIO()
    stamp.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.read()
