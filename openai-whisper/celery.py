import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whisper_project.settings')

app = Celery('whisper_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.update(
    task_time_limit=3600,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    task_default_queue='default',
)
