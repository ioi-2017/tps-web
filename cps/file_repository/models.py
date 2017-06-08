# Amir Keivan Mohtashami
# Amirmohsen Ahanchi
import hashlib

from django.db import models
from django.utils.translation import ugettext_lazy as _
import os


def get_file_name(instance, filename):
    filename = os.path.basename(filename)
    current_name = getattr(instance, "name", None)
    if not current_name:
        instance.name = filename
    return filename


class FileModel(models.Model):
    file = models.FileField(verbose_name=_("file"), upload_to=get_file_name)
    name = models.CharField(verbose_name=_("name"), max_length=256, blank=True)
    upload_date = models.DateTimeField(verbose_name=_("upload date"), auto_now_add=True)
    description = models.TextField(verbose_name=_("description"), blank=True)

    def __str__(self):
        return self.name

    def get_file_hash(self):
        self.file.open('rb')
        f = self.file
        hash = hashlib.sha1()
        if f.multiple_chunks():
            for chunk in f.chunks():
                hash.update(chunk)
        else:
            while True:
                data = f.read(1 << 20)
                if not data:
                    break
                hash.update(data)
        return hash.hexdigest()

    def get_value_as_string(self):
        self.file.open()
        try:
            return self.file.read().decode("utf-8")
        except UnicodeDecodeError:
            return self.get_file_hash()

    def get_truncated_content(self, len=255):
        content = self.file.read(len)
        content = content.decode(errors='replace')
        remained = bool(self.file.read(1))
        self.file.close()
        if remained:
            content += "..."
        return content
