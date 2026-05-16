"""
Tool: PDF Password (Protect & Unlock)
Route: POST /api/pdf-password
"""
import io
import base64
from flask import Blueprint, request, jsonify

bp = Blueprint("pdf_password", __name__)

def _ok(data):  return jsonify({"success": True, **data}), 200
def _err(msg, code=400): return jsonify({"success": False, "error": msg}), code

try:
    from pypdf import PdfWriter, PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


def _pdf_password(file_bytes: bytes, filename: str, password: str, action: str) -> dict:
    if not HAS_PYPDF:
        raise RuntimeError("pypdf not installed — run: pip install pypdf")

    if action == "protect":
        reader = PdfReader(io.BytesIO(file_bytes))
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(password)
        buf = io.BytesIO()
        writer.write(buf)
        return {
            "output_b64":      base64.b64encode(buf.getvalue()).decode(),
            "output_filename": f"protected_{filename}",
            "action":          "protected",
        }

    elif action == "unlock":
        reader = PdfReader(io.BytesIO(file_bytes))
        if reader.is_encrypted:
            success = reader.decrypt(password)
            if not success:
                raise ValueError("Incorrect password or unsupported encryption.")
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        buf = io.BytesIO()
        writer.write(buf)
        return {
            "output_b64":      base64.b64encode(buf.getvalue()).decode(),
            "output_filename": f"unlocked_{filename}",
            "action":          "unlocked",
        }
    else:
        raise ValueError(f"Unknown action: {action}")


@bp.route("/api/pdf-password", methods=["POST"])
def route_pdf_password():
    if "file" not in request.files:
        return _err("No file uploaded.")
    f      = request.files["file"]
    pwd    = request.form.get("password", "")
    action = request.form.get("action", "protect")  # protect | unlock
    if not pwd:
        return _err("Password is required.")
    try:
        return _ok(_pdf_password(f.read(), f.filename, pwd, action))
    except Exception as e:
        return _err(str(e))
