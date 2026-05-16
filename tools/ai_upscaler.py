"""
Tool: AI Image Upscaler (FSRCNN)
Route: POST /api/ai-upscale
"""
import io
import base64
import cv2
import numpy as np
from flask import Blueprint, request, jsonify
from PIL import Image
from pathlib import Path

bp = Blueprint("ai_upscaler", __name__)

# Load models on initialization to be fast
MODELS_PATH = Path(__file__).parent.parent
SR = cv2.dnn_superres.DnnSuperResImpl_create()

def _ok(data): return jsonify({"success": True, **data}), 200
def _err(msg, code=400): return jsonify({"success": False, "error": msg}), code

def _ai_upscale(file_bytes, filename, scale=2):
    # Convert bytes to opencv image
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Invalid image file")

    model_file = MODELS_PATH / f"FSRCNN_x{scale}.pb"
    
    if not model_file.exists():
        # Fallback to standard Lanczos if model missing, but we downloaded them
        # Alternatively, raise error
        raise FileNotFoundError(f"AI Model FSRCNN_x{scale} not found")

    SR.readModel(str(model_file))
    SR.setModel("fsrcnn", scale)
    
    # Run the AI upscaling
    # Note: AI upscaling can be memory intensive for large images
    upscaled = SR.upsample(img)
    
    # Convert back to bytes
    _, buffer = cv2.imencode(".png", upscaled)
    output_bytes = buffer.tobytes()
    
    orig_size = len(file_bytes)
    new_size = len(output_bytes)
    
    return {
        "output_b64": base64.b64encode(output_bytes).decode(),
        "output_filename": f"{Path(filename).stem}_ai_upscaled_x{scale}.png",
        "output_format": "PNG",
        "original_dims": f"{img.shape[1]}x{img.shape[0]}",
        "output_dims": f"{upscaled.shape[1]}x{upscaled.shape[0]}",
        "original_size_kb": round(orig_size / 1024, 2),
        "upscaled_size_kb": round(new_size / 1024, 2),
    }

@bp.route("/api/ai-upscale", methods=["POST"])
def route_ai_upscale():
    if "file" not in request.files:
        return _err("No file uploaded")
    
    f = request.files["file"]
    scale = int(request.form.get("scale", 2))
    
    if scale not in [2, 3, 4]:
        return _err("Invalid scale. Supported: 2, 3, 4")
        
    try:
        import tempfile
        import os
        
        # Security: Auto-delete uploaded files using tempfile context
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            f.save(tmp.name)
            # Read the bytes back for processing (or you could pass tmp.name to cv2)
            with open(tmp.name, 'rb') as f_tmp:
                file_bytes = f_tmp.read()
            
            result = _ai_upscale(file_bytes, f.filename, scale)
            return _ok(result)
        # file is auto-deleted after this block
    except Exception as e:
        return _err(str(e))
