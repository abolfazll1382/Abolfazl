# whisper_project/celery.py

import os
import django
from celery import Celery
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project_name')
django.setup()

# Create Celery app instance
app = Celery(
    'your_project_name',
    backend='django_celery_results.backends.database:DatabaseBackend'
)

# Load settings from Django
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Configure Celery-specific options
app.conf.update(
    task_time_limit=3600,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    task_default_queue='default',
    worker_hijack_root_logger=False,  # ✅ Prevent Celery from overriding Django logging
)

# Mute noisy Celery-related loggers
for noisy_logger in [
    "celery", "celery.app.trace", "celery.worker.strategy",
    "kombu", "billiard", "amqp"
]:
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)

