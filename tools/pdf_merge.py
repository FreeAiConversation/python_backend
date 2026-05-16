"""
Tool: PDF Merge
Route: POST /api/pdf-merge
"""
import io
import base64
from flask import Blueprint, request, jsonify

bp = Blueprint("pdf_merge", __name__)

def _ok(data):  return jsonify({"success": True, **data}), 200
def _err(msg, code=400): return jsonify({"success": False, "error": msg}), code

try:
    from pypdf import PdfWriter, PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


def _pdf_merge(files_bytes: list, filenames: list) -> dict:
    if not HAS_PYPDF:
        raise RuntimeError("pypdf not installed — run: pip install pypdf")
    writer = PdfWriter()
    for b in files_bytes:
        reader = PdfReader(io.BytesIO(b))
        for page in reader.pages:
            writer.add_page(page)
    buf = io.BytesIO()
    writer.write(buf)
    out_bytes = buf.getvalue()
    return {
        "output_b64":      base64.b64encode(out_bytes).decode(),
        "output_filename": "merged.pdf",
        "page_count":      sum(len(PdfReader(io.BytesIO(b)).pages) for b in files_bytes),
        "file_count":      len(files_bytes),
        "output_size_kb":  round(len(out_bytes) / 1024, 2),
    }


@bp.route("/api/pdf-merge", methods=["POST"])
def route_pdf_merge():
    files = request.files.getlist("files")
    if not files:
        return _err("No files uploaded. Use key 'files'.")
    
    # Check if user wants async processing (for large files)
    is_async = request.form.get("async", "false").lower() == "true"
    
    try:
        files_bytes = [f.read() for f in files]
        filenames   = [f.filename for f in files]
        
        if is_async:
            from tasks import async_pdf_merge
            task = async_pdf_merge.delay(files_bytes, filenames)
            return _ok({"task_id": task.id, "status": "processing"})
            
        return _ok(_pdf_merge(files_bytes, filenames))
    except Exception as e:
        return _err(str(e))

@bp.route("/api/pdf-merge/status/<task_id>", methods=["GET"])
def route_pdf_merge_status(task_id):
    from tasks import celery
    task = celery.AsyncResult(task_id)
    if task.state == 'PENDING':
        return _ok({"status": "waiting"})
    elif task.state == 'SUCCESS':
        return _ok({"status": "completed", "result": task.result})
    elif task.state == 'FAILURE':
        return _err(str(task.info))
    return _ok({"status": task.state, "info": str(task.info)})
