from __future__ import absolute_import

import celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cps.settings')

from django.conf import settings

app = celery.Celery('cps')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
