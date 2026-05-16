import os
import tempfile
from flask import abort

def validate_file_size(file, max_size_mb=50):
    """
    Checks if a file exceeds a specific size before processing.
    """
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > max_size_mb * 1024 * 1024:
        abort(413, f"File exceeds {max_size_mb}MB limit")

def safe_process_file(file, process_func, *args, **kwargs):
    """
    Saves a file to a secure temp location, processes it, and ensures it's deleted.
    """
    with tempfile.NamedTemporaryFile(delete=True) as tmp:
        file.save(tmp.name)
        # Mock virus scan (placeholder for ClamAV)
        if _is_malicious(tmp.name):
            abort(400, "Malicious file detected")
            
        return process_func(tmp.name, *args, **kwargs)

def _is_malicious(filepath):
    """
    Placeholder for ClamAV or VirusTotal check.
    In a real prod environment, you would use:
    import clamd
    cd = clamd.ClamdUnixSocket()
    return cd.scan(filepath) == 'FOUND'
    """
    # Simple check for very basic common malicious extensions inside archives if needed
    # For now, just return False
    return False
