"""
FreeAiConversion — Main App Entry Point
Registers all tool Blueprints + applies security layers.
"""
import argparse
from flask import Flask, jsonify
from flask_cors import CORS

# ── Security ──────────────────────────────────────────────────────────────────
from security.headers import add_security_headers
from security.limits import check_upload_limits
from security.rate_limiter import limiter, HEAVY_LIMIT, MEDIUM_LIMIT, LIGHT_LIMIT
from security.headers      import apply_security_headers

# Initialize Flask App
app = Flask(__name__)

# Register Global Security Middleware
app.before_request(check_upload_limits)
app.after_request(add_security_headers)

# ── Tool Blueprints ───────────────────────────────────────────────────────────
from tools.image_optimizer   import bp as image_optimizer_bp
from tools.watermark         import bp as watermark_bp
from tools.code_formatter    import bp as code_formatter_bp
from tools.password_generator import bp as password_generator_bp
from tools.word_counter      import bp as word_counter_bp
from tools.color_picker      import bp as color_picker_bp
from tools.pdf_merge         import bp as pdf_merge_bp
from tools.pdf_split         import bp as pdf_split_bp
from tools.pdf_compress      import bp as pdf_compress_bp
from tools.pdf_password      import bp as pdf_password_bp
from tools.pdf_watermark     import bp as pdf_watermark_bp
from tools.pdf_to_word       import bp as pdf_to_word_bp
from tools.word_to_pdf       import bp as word_to_pdf_bp
from tools.epub_to_pdf       import bp as epub_to_pdf_bp
from tools.ai_upscaler      import bp as ai_upscaler_bp

# ── Create app ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 52 * 1024 * 1024  # hard 52 MB request limit

# Whitelist only trusted domains
CORS(app, origins=[
    "http://localhost:3000",
    "http://localhost:3001",
    "https://freeaiconversion.com",
    "https://www.freeaiconversion.com",
    "https://freeaiconversion.vercel.app",
], methods=["GET", "POST", "OPTIONS"], supports_credentials=False)

# ── Attach security layers ────────────────────────────────────────────────────
limiter.init_app(app)
apply_security_headers(app)

# ── Register Blueprints ───────────────────────────────────────────────────────
app.register_blueprint(image_optimizer_bp)
app.register_blueprint(watermark_bp)
app.register_blueprint(code_formatter_bp)
app.register_blueprint(password_generator_bp)
app.register_blueprint(word_counter_bp)
app.register_blueprint(color_picker_bp)
app.register_blueprint(pdf_merge_bp)
app.register_blueprint(pdf_split_bp)
app.register_blueprint(pdf_compress_bp)
app.register_blueprint(pdf_password_bp)
app.register_blueprint(pdf_watermark_bp)
app.register_blueprint(pdf_to_word_bp)
app.register_blueprint(word_to_pdf_bp)
app.register_blueprint(epub_to_pdf_bp)
app.register_blueprint(ai_upscaler_bp)

from tools.excel_to_pdf import excel_to_pdf_bp
from tools.pdf_to_excel import pdf_to_excel_bp
app.register_blueprint(excel_to_pdf_bp)
app.register_blueprint(pdf_to_excel_bp)

# ── Apply per-route rate limits ───────────────────────────────────────────────
# Explicit rate limits for heavy tools
heavy_tools = [
    'image_optimizer.optimize_image',
    'watermark.watermark_image',
    'ai_upscaler.ai_upscale',
    'pdf_to_word.convert_pdf_to_word',
    'word_to_pdf.convert_word_to_pdf',
    'epub_to_pdf.convert_epub_to_pdf'
]

for tool_endpoint in heavy_tools:
    view_func = app.view_functions.get(tool_endpoint)
    if view_func:
        limiter.limit(HEAVY_LIMIT)(view_func)

# ── Health check ──────────────────────────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
@limiter.exempt   # health checks are never rate-limited
def health():
    return jsonify({
        "success": True,
        "status":  "running",
        "version": "2.1.0",
        "security": "enabled",
        "tools": [
            "image-optimizer", "watermark", "ai-upscaler", "code-formatter",
            "password-generator", "word-counter", "color-picker",
            "pdf-merge", "pdf-split", "pdf-compress", "pdf-password",
            "pdf-watermark", "pdf-to-word", "word-to-pdf", "epub-to-pdf",
        ],
    })

# ── Global error handlers ─────────────────────────────────────────────────────
@app.errorhandler(413)
def too_large(_):
    return jsonify({"success": False, "error": "File too large. Maximum size is 50 MB."}), 413

@app.errorhandler(429)
def rate_limited(_):
    return jsonify({"success": False, "error": "Too many requests. Please slow down."}), 429

# ── Root Landing Page ─────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
@limiter.exempt
def index():
    return jsonify({
        "success": True,
        "message": "FreeAiConversion Tools API is Active",
        "documentation": "https://freeaiconversion.com/docs",
        "status": "online",
        "author": "Antigravity AI Engine"
    })

@app.errorhandler(404)
def not_found(_):
    return jsonify({"success": False, "error": "Endpoint not found."}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"success": False, "error": "Internal server error."}), 500


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host",  default="0.0.0.0")
    parser.add_argument("--port",  default=5000, type=int)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    sep = "=" * 58
    print(f"\n{sep}")
    print("  FREEAICONVERSION - Python Tools API v2.0")
    print(f"  Security: Rate limiting + Headers + Validation")
    print(sep)
    print(f"  Host  : {args.host}:{args.port}")
    print(f"  Debug : {args.debug}")
    print(f"{sep}\n")

    app.run(host=args.host, port=args.port, debug=args.debug)
