import os
import time
from celery import Celery
from tools.pdf_merge import _pdf_merge
from tools.image_optimizer import _optimize_image

# REDIS_URL should be in environment
redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery = Celery(
    "tasks",
    broker=redis_url,
    backend=redis_url
)

@celery.task(bind=True)
def async_pdf_merge(self, files_bytes, filenames):
    """Heavy PDF merging task"""
    self.update_state(state='PROGRESS', meta={'status': 'Merging pages...'})
    return _pdf_merge(files_bytes, filenames)

@celery.task(bind=True)
def async_image_optimize(self, file_bytes, filename, quality):
    """Heavy Image optimization task"""
    self.update_state(state='PROGRESS', meta={'status': 'Optimizing pixels...'})
    return _optimize_image(file_bytes, filename, quality)
