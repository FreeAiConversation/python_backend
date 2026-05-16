"""
Tool: PDF Split
Routes: POST /api/pdf-split
"""
import io
import re
import base64
import zipfile
from flask import Blueprint, request, jsonify

bp = Blueprint("pdf_split", __name__)

def _ok(data):  return jsonify({"success": True, **data}), 200
def _err(msg, code=400): return jsonify({"success": False, "error": msg}), code

try:
    from pypdf import PdfWriter, PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


def _parse_ranges(ranges_str: str, total_pages: int) -> list:
    """Parse '1,3-5,7' → list of 0-based page indices."""
    pages = set()
    for part in ranges_str.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            pages.update(range(int(a) - 1, int(b)))
        elif part.isdigit():
            pages.add(int(part) - 1)
    return sorted(p for p in pages if 0 <= p < total_pages)


def _pdf_split(file_bytes: bytes, filename: str, ranges: str) -> dict:
    if not HAS_PYPDF:
        raise RuntimeError("pypdf not installed — run: pip install pypdf")
    reader = PdfReader(io.BytesIO(file_bytes))
    total  = len(reader.pages)
    if ranges == "all":
        page_indices = list(range(total))
    else:
        page_indices = _parse_ranges(ranges, total)
    if not page_indices:
        raise ValueError("No valid pages selected.")
    writer = PdfWriter()
    for i in page_indices:
        writer.add_page(reader.pages[i])
    buf = io.BytesIO()
    writer.write(buf)
    stem = filename.rsplit(".", 1)[0]
    return {
        "output_b64":      base64.b64encode(buf.getvalue()).decode(),
        "output_filename": f"{stem}_pages.pdf",
        "pages_extracted": len(page_indices),
        "total_pages":     total,
    }


def _pdf_split_multiple(file_bytes: bytes, filename: str) -> dict:
    """Split every page into its own PDF and return a ZIP."""
    if not HAS_PYPDF:
        raise RuntimeError("pypdf not installed — run: pip install pypdf")
    reader = PdfReader(io.BytesIO(file_bytes))
    total  = len(reader.pages)
    stem   = filename.rsplit(".", 1)[0]
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            pdf_buf = io.BytesIO()
            writer.write(pdf_buf)
            zf.writestr(f"{stem}_page_{i+1}.pdf", pdf_buf.getvalue())
    return {
        "output_b64":      base64.b64encode(zip_buf.getvalue()).decode(),
        "output_filename": f"{stem}_all_pages.zip",
        "output_type":     "zip",
        "pages_extracted": total,
        "total_pages":     total,
    }


@bp.route("/api/pdf-split", methods=["POST"])
def route_pdf_split():
    if "file" not in request.files:
        return _err("No file uploaded.")
    f          = request.files["file"]
    ranges     = request.form.get("ranges", "all")
    split_type = request.form.get("type", "single")  # single | multiple
    try:
        if split_type == "multiple" and ranges == "all":
            result = _pdf_split_multiple(f.read(), f.filename)
        else:
            result = _pdf_split(f.read(), f.filename, ranges)
        return _ok(result)
    except Exception as e:
        return _err(str(e))
