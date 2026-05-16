"""
Production server using Waitress — lightweight, no C compiler needed.
Much faster than Flask's dev server. Works on Windows, Linux, Mac.

Usage:
    pip install waitress
    python run.py
"""
from waitress import serve
from app import app

HOST    = "0.0.0.0"
PORT    = 5000
THREADS = 8  # concurrent request threads (increase for high traffic)

print(f"\n🚀  FreeAiConversion API  →  http://{HOST}:{PORT}")
print(f"    Threads : {THREADS}")
print(f"    Mode    : Production (Waitress)\n")

serve(app, host=HOST, port=PORT, threads=THREADS)
