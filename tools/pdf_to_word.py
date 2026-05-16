"""
Tool: PDF to Word
Route: POST /api/pdf-to-word
"""
import io
import os
import base64
import tempfile
from pathlib import Path
from flask import Blueprint, request, jsonify

bp = Blueprint("pdf_to_word", __name__)

def _ok(data):  return jsonify({"success": True, **data}), 200
def _err(msg, code=400): return jsonify({"success": False, "error": msg}), code

try:
    from pdf2docx import Converter
    HAS_PDF2DOCX = True
except ImportError:
    HAS_PDF2DOCX = False


def _pdf_to_word(file_bytes: bytes, filename: str) -> dict:
    if not HAS_PDF2DOCX:
        raise RuntimeError("pdf2docx not installed — run: pip install pdf2docx")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        tf.write(file_bytes)
        pdf_path = tf.name

    docx_path = pdf_path.replace(".pdf", ".docx")
    try:
        cv = Converter(pdf_path)
        cv.convert(docx_path, start=0, end=None)
        cv.close()
        with open(docx_path, "rb") as f:
            out_bytes = f.read()
        return {
            "output_b64":      base64.b64encode(out_bytes).decode(),
            "output_filename": f"{Path(filename).stem}.docx",
        }
    finally:
        if os.path.exists(pdf_path):  os.remove(pdf_path)
        if os.path.exists(docx_path): os.remove(docx_path)


@bp.route("/api/pdf-to-word", methods=["POST"])
def route_pdf_to_word():
    if "file" not in request.files:
        return _err("No file uploaded.")
    f = request.files["file"]
    try:
        return _ok(_pdf_to_word(f.read(), f.filename))
    except Exception as e:
        return _err(str(e))
