"""
Security: Response Headers
Adds hardened HTTP security headers to every response.
"""
from flask import Flask


def apply_security_headers(app: Flask) -> None:
    """Register after_request hook that injects security headers."""

    @app.after_request
    def add_headers(response):
        # Prevent browsers from MIME-sniffing away from declared type
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Block clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Force HTTPS in production (comment out for local dev if needed)
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains; preload"
        )

        # Stop referrer leakage
        response.headers["Referrer-Policy"] = "no-referrer"

        # Block browser features we don't use
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        # Remove server fingerprint
        response.headers.pop("Server", None)
        response.headers.pop("X-Powered-By", None)

        return response
