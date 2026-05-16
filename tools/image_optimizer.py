"""
Tool: Image Optimizer
Route: POST /api/image-optimizer
"""
import io
import base64
from pathlib import Path
from flask import Blueprint, request, jsonify
from PIL import Image
import pillow_avif
bp = Blueprint("image_optimizer", __name__)


def _ok(data):
    return jsonify({"success": True, **data}), 200

def _err(msg, code=400):
    return jsonify({"success": False, "error": msg}), code


def _optimize_image_bytes(
    file_bytes: bytes,
    filename: str,
    quality: int = 75,
    output_format: str = None,
    max_width: int = None,
    max_height: int = None,
    upscale: int = 1,
    strip_metadata: bool = True,
) -> dict:
    img = Image.open(io.BytesIO(file_bytes))
    orig_fmt = img.format or "JPEG"
    orig_size_bytes = len(file_bytes)
    orig_wh = img.size

    fmt = (output_format or orig_fmt).upper()
    if fmt not in ("JPEG", "PNG", "WEBP", "TIFF", "BMP", "ICO", "GIF", "AVIF"):
        fmt = "JPEG"

    # Handle transparency conversions
    if fmt in ("JPEG", "BMP") and img.mode in ("RGBA", "P", "LA"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
        img = bg
    elif fmt in ("JPEG", "BMP") and img.mode != "RGB":
        img = img.convert("RGB")

    if max_width or max_height:
        w, h = img.size
        tw, th = max_width or w, max_height or h
        ratio = min(tw / w, th / h)
        if ratio < 1.0:
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
            
    if upscale and upscale > 1:
        w, h = img.size
        new_w, new_h = w * upscale, h * upscale
        # Max out around 8K resolution to prevent memory crashes
        if new_w > 7680 or new_h > 4320:
            ratio = min(7680 / w, 4320 / h)
            new_w, new_h = int(w * ratio), int(h * ratio)
        img = img.resize((new_w, new_h), Image.LANCZOS)

    if strip_metadata:
        clean = Image.new(img.mode, img.size)
        clean.putdata(list(img.getdata()))
        img = clean

    save_kwargs = {}
    if fmt == "JPEG":
        save_kwargs = {"quality": quality, "optimize": True, "progressive": True}
    elif fmt == "PNG":
        compress_level = max(0, min(9, int((100 - quality) / 11)))
        save_kwargs = {"compress_level": compress_level, "optimize": True}
    elif fmt == "WEBP":
        save_kwargs = {"quality": quality, "method": 6}
    elif fmt == "TIFF":
        save_kwargs = {"compression": "tiff_lzw"}
    elif fmt == "ICO":
        # ICO needs strict square sizes typically, but pillow handles auto-resizing if we pass sizes.
        # Let's just pass standard icon sizes.
        save_kwargs = {"sizes": [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]}
    elif fmt == "AVIF":
        save_kwargs = {"quality": quality}

    buf = io.BytesIO()
    img.save(buf, format=fmt, **save_kwargs)
    output_bytes = buf.getvalue()

    saved = orig_size_bytes - len(output_bytes)
    saved_pct = round((saved / orig_size_bytes) * 100, 1) if orig_size_bytes else 0

    ext_map = {
        "JPEG": "jpg", "PNG": "png", "WEBP": "webp", 
        "TIFF": "tiff", "BMP": "bmp", "ICO": "ico", "GIF": "gif", "AVIF": "avif"
    }
    stem = Path(filename).stem
    out_name = f"{stem}_optimized.{ext_map.get(fmt, 'jpg')}"

    return {
        "output_b64":        base64.b64encode(output_bytes).decode(),
        "output_filename":   out_name,
        "output_format":     fmt,
        "original_size_kb":  round(orig_size_bytes / 1024, 2),
        "optimized_size_kb": round(len(output_bytes) / 1024, 2),
        "saved_kb":          round(saved / 1024, 2),
        "saved_percent":     saved_pct,
        "original_dims":     f"{orig_wh[0]}×{orig_wh[1]}",
        "output_dims":       f"{img.size[0]}×{img.size[1]}",
        "quality_used":      quality,
    }


@bp.route("/api/image-optimizer", methods=["POST"])
def route_image_optimizer():
    if "file" not in request.files:
        return _err("No file uploaded. Use key 'file'.")
    f = request.files["file"]
    quality = int(request.form.get("quality", 75))
    fmt = request.form.get("format", None)
    mw = request.form.get("max_width", None)
    mh = request.form.get("max_height", None)
    upscale = int(request.form.get("upscale", 1))
    try:
        result = _optimize_image_bytes(
            file_bytes=f.read(), filename=f.filename,
            quality=quality, output_format=fmt,
            max_width=int(mw) if mw else None,
            max_height=int(mh) if mh else None,
            upscale=upscale,
        )
        return _ok(result)
    except Exception as e:
        return _err(str(e))
