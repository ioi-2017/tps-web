# Amir Keivan Mohtashami

from django.db import models
from django.utils.translation import ugettext_lazy as _


class FileModel(models.Model):
    file = models.FileField(verbose_name=_("file"))
    upload_date = models.DateTimeField(verbose_name=_("upload date"), auto_now_add=True)
    description = models.TextField(verbose_name=_("description"), blank=True)
