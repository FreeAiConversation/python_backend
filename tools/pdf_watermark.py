"""
Tool: PDF Watermark (Text & Image)
Route: POST /api/pdf-watermark
"""
import io
import base64
from flask import Blueprint, request, jsonify

bp = Blueprint("pdf_watermark", __name__)

def _ok(data):  return jsonify({"success": True, **data}), 200
def _err(msg, code=400): return jsonify({"success": False, "error": msg}), code

try:
    from pypdf import PdfWriter, PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


def _pdf_watermark_text(file_bytes: bytes, filename: str, text: str) -> dict:
    if not HAS_PYPDF or not HAS_REPORTLAB:
        raise RuntimeError("pypdf or reportlab not installed")

    reader = PdfReader(io.BytesIO(file_bytes))
    writer = PdfWriter()

    for page in reader.pages:
        width  = float(page.mediabox.width)
        height = float(page.mediabox.height)

        wm_buf = io.BytesIO()
        c = canvas.Canvas(wm_buf, pagesize=(width, height))
        c.saveState()
        c.setFont("Helvetica-Bold", 48)
        c.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.35)
        c.translate(width / 2, height / 2)
        c.rotate(45)
        c.drawCentredString(0, 0, text)
        c.restoreState()
        c.save()

        wm_reader = PdfReader(io.BytesIO(wm_buf.getvalue()))
        page.merge_page(wm_reader.pages[0])
        writer.add_page(page)

    buf = io.BytesIO()
    writer.write(buf)
    return {
        "output_b64":      base64.b64encode(buf.getvalue()).decode(),
        "output_filename": f"watermarked_{filename}",
    }


def _pdf_watermark_image(file_bytes: bytes, filename: str, image_bytes: bytes) -> dict:
    if not HAS_PYPDF or not HAS_REPORTLAB:
        raise RuntimeError("pypdf or reportlab not installed")

    from reportlab.lib.utils import ImageReader

    reader = PdfReader(io.BytesIO(file_bytes))
    writer = PdfWriter()

    for page in reader.pages:
        width  = float(page.mediabox.width)
        height = float(page.mediabox.height)

        img_temp_buf = io.BytesIO()
        c = canvas.Canvas(img_temp_buf, pagesize=(width, height))
        img_reader = ImageReader(io.BytesIO(image_bytes))
        img_w, img_h = img_reader.getSize()
        aspect = img_h / img_w
        new_w  = width * 0.4
        new_h  = new_w * aspect
        c.saveState()
        c.setFillAlpha(0.3)
        c.drawImage(img_reader, (width - new_w)/2, (height - new_h)/2,
                    width=new_w, height=new_h, mask='auto')
        c.restoreState()
        c.save()

        wm_reader = PdfReader(io.BytesIO(img_temp_buf.getvalue()))
        page.merge_page(wm_reader.pages[0])
        writer.add_page(page)

    buf = io.BytesIO()
    writer.write(buf)
    return {
        "output_b64":      base64.b64encode(buf.getvalue()).decode(),
        "output_filename": f"watermarked_{filename}",
    }


@bp.route("/api/pdf-watermark", methods=["POST"])
def route_pdf_watermark():
    if "file" not in request.files:
        return _err("No file uploaded.")
    f          = request.files["file"]
    text       = request.form.get("text")
    image_file = request.files.get("image")
    try:
        if image_file:
            result = _pdf_watermark_image(f.read(), f.filename, image_file.read())
        else:
            result = _pdf_watermark_text(f.read(), f.filename, text or "CONFIDENTIAL")
        return _ok(result)
    except Exception as e:
        return _err(str(e))
