"""
Tool: EPUB to PDF
Route: POST /api/epub-to-pdf
"""
import io
import os
import base64
import tempfile
from pathlib import Path
from flask import Blueprint, request, jsonify

bp = Blueprint("epub_to_pdf", __name__)

def _ok(data):  return jsonify({"success": True, **data}), 200
def _err(msg, code=400): return jsonify({"success": False, "error": msg}), code

try:
    import ebooklib
    from ebooklib import epub
    HAS_EBOOKLIB = True
except ImportError:
    HAS_EBOOKLIB = False

try:
    from xhtml2pdf import pisa
    HAS_PISA = True
except ImportError:
    HAS_PISA = False


def _epub_to_pdf(file_bytes: bytes, filename: str) -> dict:
    if not HAS_EBOOKLIB or not HAS_PISA:
        raise RuntimeError(
            "ebooklib or xhtml2pdf not installed — "
            "run: pip install ebooklib xhtml2pdf"
        )

    with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tf:
        tf.write(file_bytes)
        epub_path = tf.name

    try:
        book = epub.read_epub(epub_path)
        full_html = "<html><body>"
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                full_html += item.get_content().decode("utf-8", errors="ignore")
        full_html += "</body></html>"

        pdf_buf = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.BytesIO(full_html.encode("utf-8")), dest=pdf_buf)
        if pisa_status.err:
            raise RuntimeError("PDF generation failed inside xhtml2pdf.")

        out_bytes = pdf_buf.getvalue()
        return {
            "output_b64":      base64.b64encode(out_bytes).decode(),
            "output_filename": f"{Path(filename).stem}.pdf",
        }
    finally:
        if os.path.exists(epub_path): os.remove(epub_path)


@bp.route("/api/epub-to-pdf", methods=["POST"])
def route_epub_to_pdf():
    if "file" not in request.files:
        return _err("No file uploaded.")
    f = request.files["file"]
    try:
        return _ok(_epub_to_pdf(f.read(), f.filename))
    except Exception as e:
        return _err(str(e))
