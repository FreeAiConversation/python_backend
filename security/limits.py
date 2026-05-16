import os
from flask import request, abort

MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit

def check_upload_limits():
    """
    Prevents Denial of Service (DoS) attacks by enforcing 
    strict file size and content-length headers.
    """
    content_length = request.content_length
    if content_length and content_length > MAX_CONTENT_LENGTH:
        abort(413, "File too large. Maximum size allowed is 16MB.")

def sanitize_filename_hardened(filename):
    """
    Hardened filename sanitization to prevent Path Traversal 
    and command injection Trojans.
    """
    from werkzeug.utils import secure_filename
    clean_name = secure_filename(filename)
    # Remove any possible hidden characters or suspicious dots
    clean_name = clean_name.replace("..", "").replace("/", "").replace("\\", "")
    return clean_name
