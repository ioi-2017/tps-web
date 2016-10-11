# Amir Keivan Mohtashami
# Amirmohsen Ahanchi

from django.db import models
from django.utils.translation import ugettext_lazy as _
import os


def get_file_name(instance, filename):
    filename = os.path.basename(filename)
    instance.name = filename
    return filename


class FileModel(models.Model):
    file = models.FileField(verbose_name=_("file"), upload_to=get_file_name)
    name = models.CharField(verbose_name=_("name"), max_length=256, blank=True, editable=False)
    upload_date = models.DateTimeField(verbose_name=_("upload date"), auto_now_add=True)
    description = models.TextField(verbose_name=_("description"), blank=True)

    def __str__(self):
        return self.name
