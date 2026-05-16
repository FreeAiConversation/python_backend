import os
from celery import Celery

def make_celery(app_name):
    # REDIS_URL should be in environment
    # Defaulting to localhost for development
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    
    return Celery(
        app_name,
        backend=redis_url,
        broker=redis_url
    )

# usage in app.py:
# celery = make_celery(__name__)
