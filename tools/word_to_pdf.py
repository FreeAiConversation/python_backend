"""
Tool: Word to PDF
Route: POST /api/word-to-pdf
"""
import io
import os
import base64
import tempfile
from pathlib import Path
from flask import Blueprint, request, jsonify

bp = Blueprint("word_to_pdf", __name__)

def _ok(data):  return jsonify({"success": True, **data}), 200
def _err(msg, code=400): return jsonify({"success": False, "error": msg}), code

try:
    from docx2pdf import convert as docx_convert
    HAS_DOCX2PDF = True
except ImportError:
    HAS_DOCX2PDF = False


def _word_to_pdf(file_bytes: bytes, filename: str) -> dict:
    if not HAS_DOCX2PDF:
        raise RuntimeError(
            "docx2pdf not installed — run: pip install docx2pdf\n"
            "Note: Microsoft Word must be installed on the server for this to work."
        )

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
        tf.write(file_bytes)
        docx_path = tf.name

    pdf_path = docx_path.replace(".docx", ".pdf")
    try:
        docx_convert(docx_path, pdf_path)
        with open(pdf_path, "rb") as f:
            out_bytes = f.read()
        return {
            "output_b64":      base64.b64encode(out_bytes).decode(),
            "output_filename": f"{Path(filename).stem}.pdf",
        }
    finally:
        if os.path.exists(docx_path): os.remove(docx_path)
        if os.path.exists(pdf_path):  os.remove(pdf_path)


@bp.route("/api/word-to-pdf", methods=["POST"])
def route_word_to_pdf():
    if "file" not in request.files:
        return _err("No file uploaded.")
    f = request.files["file"]
    try:
        return _ok(_word_to_pdf(f.read(), f.filename))
    except Exception as e:
        return _err(str(e))
