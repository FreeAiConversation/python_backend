"""
Tool: PDF Compress
Route: POST /api/pdf-compress
"""
import io
import base64
from flask import Blueprint, request, jsonify

bp = Blueprint("pdf_compress", __name__)

def _ok(data):  return jsonify({"success": True, **data}), 200
def _err(msg, code=400): return jsonify({"success": False, "error": msg}), code

try:
    from pypdf import PdfWriter, PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


def _pdf_compress(file_bytes: bytes, filename: str) -> dict:
    if not HAS_PYPDF:
        raise RuntimeError("pypdf not installed — run: pip install pypdf")
    reader = PdfReader(io.BytesIO(file_bytes))
    writer = PdfWriter()
    for page in reader.pages:
        page.compress_content_streams()
        writer.add_page(page)
    buf = io.BytesIO()
    writer.write(buf)
    out_bytes       = buf.getvalue()
    original_kb     = round(len(file_bytes) / 1024, 2)
    compressed_kb   = round(len(out_bytes) / 1024, 2)
    saved_pct       = round((1 - len(out_bytes) / len(file_bytes)) * 100, 1) if file_bytes else 0
    return {
        "output_b64":        base64.b64encode(out_bytes).decode(),
        "output_filename":   f"compressed_{filename}",
        "original_size_kb":  original_kb,
        "compressed_size_kb":compressed_kb,
        "saved_percent":     max(0, saved_pct),
    }


@bp.route("/api/pdf-compress", methods=["POST"])
def route_pdf_compress():
    if "file" not in request.files:
        return _err("No file uploaded.")
    f = request.files["file"]
    try:
        return _ok(_pdf_compress(f.read(), f.filename))
    except Exception as e:
        return _err(str(e))
