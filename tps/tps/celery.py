from __future__ import absolute_import

import celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tps.settings')

from tasks.serializers import DjangoPKSerializer

DjangoPKSerializer.register()

app = celery.Celery('tps')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
