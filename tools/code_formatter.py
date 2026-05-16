"""
Tool: Code Formatter
Route: POST /api/code-formatter
"""
import re
import json
from flask import Blueprint, request, jsonify

bp = Blueprint("code_formatter", __name__)

def _ok(data):  return jsonify({"success": True, **data}), 200
def _err(msg, code=400): return jsonify({"success": False, "error": msg}), code

try:
    import jsbeautifier
    HAS_JSBEAUTIFIER = True
except ImportError:
    HAS_JSBEAUTIFIER = False

try:
    import sqlparse
    HAS_SQLPARSE = True
except ImportError:
    HAS_SQLPARSE = False


def _format_json(code: str, indent: int = 2, **_) -> str:
    parsed = json.loads(code)
    return json.dumps(parsed, indent=indent, sort_keys=False, ensure_ascii=False)

def _format_js(code: str, indent: int = 2, **_) -> str:
    if not HAS_JSBEAUTIFIER: raise RuntimeError("jsbeautifier not installed")
    opts = jsbeautifier.default_options()
    opts.indent_size = indent
    opts.end_with_newline = True
    return jsbeautifier.beautify(code, opts)

def _format_html(code: str, indent: int = 2, **_) -> str:
    if not HAS_JSBEAUTIFIER: raise RuntimeError("jsbeautifier not installed")
    import jsbeautifier.html as hb
    opts = jsbeautifier.default_options()
    opts.indent_size = indent
    return hb.beautify(code, opts)

def _format_css(code: str, indent: int = 2, **_) -> str:
    if HAS_JSBEAUTIFIER:
        try:
            import jsbeautifier.css as cb
            opts = jsbeautifier.default_options()
            opts.indent_size = indent
            return cb.beautify(code, opts)
        except ImportError:
            pass
    code = re.sub(r'\s+', ' ', code).strip()
    code = re.sub(r'\s*{\s*', ' {\n' + ' ' * indent, code)
    code = re.sub(r'\s*}\s*', '\n}\n\n', code)
    code = re.sub(r';\s*', ';\n' + ' ' * indent, code)
    code = re.sub(r',\s*([^{])', r',\n\1', code)
    return code.strip()

def _format_sql(code: str, indent: int = 2, **_) -> str:
    if not HAS_SQLPARSE: raise RuntimeError("sqlparse not installed")
    return sqlparse.format(code, reindent=True, keyword_case="upper", indent_width=indent)

_FORMATTERS = {
    "json": _format_json, "javascript": _format_js, "js": _format_js,
    "typescript": _format_js, "ts": _format_js, "html": _format_html,
    "css": _format_css, "scss": _format_css, "sql": _format_sql,
}

def _format_code(code: str, language: str, indent: int = 2) -> str:
    lang = language.lower()
    if lang not in _FORMATTERS: raise ValueError(f"Unsupported language: {lang}")
    return _FORMATTERS[lang](code, indent=indent)


@bp.route("/api/code-formatter", methods=["POST"])
def route_code_formatter():
    body = request.get_json(silent=True) or {}
    code     = body.get("code", "")
    language = body.get("language", "javascript")
    indent   = int(body.get("indent", 2))
    if not code: return _err("No code provided.")
    try:
        formatted = _format_code(code, language, indent)
        return _ok({"formatted": formatted, "language": language, "indent": indent})
    except Exception as e:
        return _err(str(e))
