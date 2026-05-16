"""
Security: Input Sanitizer
Strips dangerous characters from text inputs before processing.
Prevents: XSS payloads in watermark text, code injection via filenames, etc.
"""
import re
import os
from pathlib import Path


# ── Text sanitizer (for watermark text, code snippets, etc.) ─────────────────
_DANGEROUS_PATTERNS = re.compile(
    r"(<script|<iframe|javascript:|data:text/html|vbscript:|onload=|onerror=)",
    re.IGNORECASE,
)

def sanitize_text(value: str, max_length: int = 500) -> str:
    """Strip XSS payloads and limit length."""
    if not isinstance(value, str):
        return ""
    cleaned = _DANGEROUS_PATTERNS.sub("", value)
    return cleaned[:max_length].strip()


# ── Filename sanitizer ────────────────────────────────────────────────────────
_UNSAFE_CHARS = re.compile(r'[^\w\s\-.]')
_DOTDOT       = re.compile(r'\.\.+')

def sanitize_filename(filename: str) -> str:
    """
    Remove path traversal sequences and dangerous characters.
    e.g. '../../etc/passwd' → 'etc_passwd'
    """
    if not filename:
        return "upload"
    # Take only the base name — strip any directory component
    name = Path(filename).name
    # Remove path traversal
    name = _DOTDOT.sub(".", name)
    # Remove non-alphanumeric except dash, dot, underscore
    name = _UNSAFE_CHARS.sub("_", name)
    # Limit length
    stem, *ext_parts = name.rsplit(".", 1)
    ext  = f".{ext_parts[0]}" if ext_parts else ""
    return f"{stem[:80]}{ext}"


# ── Integer / param sanitizer ─────────────────────────────────────────────────
def safe_int(value, default: int = 0, min_val: int = None, max_val: int = None) -> int:
    """Parse integer safely with optional bounds."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    if min_val is not None: n = max(n, min_val)
    if max_val is not None: n = min(n, max_val)
    return n
