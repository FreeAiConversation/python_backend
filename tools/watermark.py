"""
Tool: Watermark Generator (Image)
Route: POST /api/watermark
"""
import io
import math
import base64
from pathlib import Path
from flask import Blueprint, request, jsonify
from PIL import Image, ImageDraw, ImageFont

bp = Blueprint("watermark", __name__)

def _ok(data):  return jsonify({"success": True, **data}), 200
def _err(msg, code=400): return jsonify({"success": False, "error": msg}), code

WATERMARK_POSITIONS = {
    "top-left":      (0.02, 0.02), "top-center":    (0.50, 0.02),
    "top-right":     (0.98, 0.02), "center-left":   (0.02, 0.50),
    "center":        (0.50, 0.50), "center-right":  (0.98, 0.50),
    "bottom-left":   (0.02, 0.98), "bottom-center": (0.50, 0.98),
    "bottom-right":  (0.98, 0.98),
}

def _hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple:
    h = hex_color.lstrip("#")
    if len(h) == 3: h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha

def _load_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            try: return ImageFont.truetype(c, size)
            except Exception: pass
    return ImageFont.load_default()

def _add_watermark_bytes(
    file_bytes, filename, watermark_type="text",
    # Text params
    text="© WATERMARK", font_size=40, color="#FFFFFF", 
    # Image params
    logo_bytes=None,
    # Common params
    pos_x=0.5, pos_y=0.5, scale=1.0, opacity=50, rotation=0,
    tile=False, tile_spacing=150, shadow=True,
) -> dict:
    img = Image.open(io.BytesIO(file_bytes)).convert("RGBA")
    w, h = img.size
    alpha_val = max(0, min(255, int(opacity * 2.55)))
    
    # ── 1. Create the base Watermark Layer (Text or Image) ──
    if watermark_type == "image" and logo_bytes:
        logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
        # Scale logo relative to base image width (scale=1.0 means 20% of image width)
        base_lw = int(w * 0.2 * scale)
        if base_lw == 0: base_lw = 10
        ratio = base_lw / logo.width
        base_lh = int(logo.height * ratio)
        logo = logo.resize((base_lw, base_lh), Image.LANCZOS)
        
        # Apply opacity to logo
        if alpha_val < 255:
            r, g, b, a = logo.split()
            a = a.point(lambda p: int(p * (alpha_val / 255.0)))
            logo = Image.merge("RGBA", (r, g, b, a))
            
        layer = logo
    else:
        text_color = _hex_to_rgba(color, alpha_val)
        shadow_color = (0, 0, 0, max(0, int(alpha_val * 0.6)))
        # Scale font size based on image size and scale param (base size = 40)
        actual_font_size = int((w / 1000) * font_size * scale)
        if actual_font_size < 10: actual_font_size = 10
        
        font = _load_font(actual_font_size)
        dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        bbox = dummy.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        
        diag = int(math.sqrt(tw**2 + th**2)) + 10
        layer = Image.new("RGBA", (diag, diag), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        cx, cy = diag // 2, diag // 2
        if shadow:
            draw.text((cx - tw//2 + 2, cy - th//2 + 2), text, font=font, fill=shadow_color, anchor="mm")
        draw.text((cx - tw//2, cy - th//2), text, font=font, fill=text_color, anchor="mm")
        
    # Apply rotation
    if rotation:
        layer = layer.rotate(rotation, resample=Image.BICUBIC, expand=True)

    lw, lh = layer.size

    # ── 2. Apply to Main Image (Tiled or Absolute) ──
    if tile:
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        step_x = lw + tile_spacing
        step_y = lh + tile_spacing
        for ty in range(-lh, h + lh, step_y):
            for tx in range(-lw, w + lw, step_x):
                overlay.paste(layer, (tx, ty), layer)
        result = Image.alpha_composite(img, overlay)
    else:
        # Calculate absolute px from relative (0.0 - 1.0) coordinates
        # pos_x and pos_y represent the CENTER of the watermark
        px = int(w * pos_x)
        py = int(h * pos_y)
        
        paste_x = px - lw // 2
        paste_y = py - lh // 2
        
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        overlay.paste(layer, (paste_x, paste_y), layer)
        result = Image.alpha_composite(img, overlay)

    buf = io.BytesIO()
    orig_ext = Path(filename).suffix.lower()
    if orig_ext in (".jpg", ".jpeg"):
        result = result.convert("RGB")
        result.save(buf, "JPEG", quality=95)
        out_name = Path(filename).stem + "_watermarked.jpg"
    else:
        result.save(buf, "PNG")
        out_name = Path(filename).stem + "_watermarked.png"

    return {
        "output_b64": base64.b64encode(buf.getvalue()).decode(),
        "output_filename": out_name,
        "image_size": f"{w}×{h}"
    }

@bp.route("/api/watermark", methods=["POST"])
def route_watermark():
    if "file" not in request.files:
        return _err("No file uploaded.")
    
    f = request.files["file"]
    watermark_type = request.form.get("watermark_type", "text")
    text = request.form.get("text", "© WATERMARK")
    font_size = float(request.form.get("font_size", 40))
    color = request.form.get("color", "#FFFFFF")
    opacity = int(request.form.get("opacity", 50))
    rotation = int(request.form.get("rotation", 0))
    tile = request.form.get("tile", "false").lower() == "true"
    tile_spacing = int(request.form.get("tile_spacing", 150))
    
    pos_x = float(request.form.get("pos_x", 0.5))
    pos_y = float(request.form.get("pos_y", 0.5))
    scale = float(request.form.get("scale", 1.0))

    logo_bytes = None
    if watermark_type == "image" and "logo" in request.files:
        logo_bytes = request.files["logo"].read()

    try:
        result = _add_watermark_bytes(
            f.read(), f.filename, 
            watermark_type=watermark_type,
            text=text, font_size=font_size, color=color, 
            logo_bytes=logo_bytes,
            pos_x=pos_x, pos_y=pos_y, scale=scale, 
            opacity=opacity, rotation=rotation, 
            tile=tile, tile_spacing=tile_spacing,
        )
        return _ok(result)
    except Exception as e:
        return _err(str(e))

