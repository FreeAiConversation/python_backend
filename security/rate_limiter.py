"""
Security: Rate Limiter
Prevents API abuse — limits requests per IP address.
Uses in-memory storage (zero dependencies beyond flask-limiter).
"""
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Use Redis if REDIS_URL is provided, otherwise fallback to in-memory
# Example: redis://localhost:6379
storage_uri = os.environ.get("REDIS_URL", "memory://")

# ── Limiter instance (attached to app in app.py) ──────────────────────────────
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "60 per hour"],
    storage_uri=storage_uri,
)

# ── Per-route limit decorators (import and apply in app.py) ───────────────────
HEAVY_LIMIT   = "10 per minute"   # PDF conversion, image processing
MEDIUM_LIMIT  = "30 per minute"   # merge, split, compress
LIGHT_LIMIT   = "60 per minute"   # password gen, color picker, word counter
