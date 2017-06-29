# Amir Keivan Mohtashami
# Amirmohsen Ahanchi
import hashlib

from django.db import models
from django.utils.translation import ugettext_lazy as _
import os

from git_orm import models as git_models, GitError

from django.core.files import File as DjangoFile

from git_orm.models.fields import Field


class FileModelMixin(object):
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
        self.file.open()
        content = self.file.read(len)
        content = content.decode(errors='replace')
        remained = bool(self.file.read(1))
        self.file.close()
        if remained:
            content += "..."
        return content


def get_file_name(instance, filename):
    filename = os.path.basename(filename)
    current_name = getattr(instance, "name", None)
    if not current_name:
        instance.name = filename
    return filename


class FileModel(models.Model, FileModelMixin):
    file = models.FileField(verbose_name=_("file"), upload_to=get_file_name)
    name = models.CharField(verbose_name=_("name"), max_length=256, blank=True)
    upload_date = models.DateTimeField(verbose_name=_("upload date"), auto_now_add=True)
    description = models.TextField(verbose_name=_("description"), blank=True)


class DummyFileDescriptor(object):
    def __init__(self, git_file):
        self.git_file = git_file
        self.pointer = 0

    def read(self, size=None):
        if size:
            new_pointer = min(len(self.git_file.content), self.pointer + size)
        else:
            new_pointer = len(self.git_file.content)
        ret_content = self.git_file.content[self.pointer:new_pointer]
        self.pointer = new_pointer
        return ret_content

    def seek(self, ptr):
        self.pointer = ptr

    def open(self):
        self.seek(0)

    def close(self):
        self.seek(len(self.git_file.content))

    def save(self, fobj):
        fobj.open()
        self.git_file.content = fobj.read()
        self.git_file.save()

    def multiple_chunks(self):
        return False

    def chunks(self):
        yield self.read()

    def __iter__(self):
        if self.multiple_chunks():
            raise NotImplementedError
        for chunk in self.chunks():
            for line in chunk.splitlines(True):
                yield line


class GitFile(git_models.Model, FileModelMixin):
    name = models.CharField(verbose_name=_("name"), max_length=256, blank=True, primary_key=True)
    content = models.TextField(verbose_name=_("content"))

    @property
    def file(self):
        return DummyFileDescriptor(self)

    def dump(self, include_hidden=False, include_pk=True):
        field = self._meta.get_field('content')
        return field.get_prep_value(self.content)

    def load(self, data):
        field = self._meta.get_field('content')
        self.content = field.to_python(data)


class GitBinaryFile(git_models.Model, FileModelMixin):
    name = models.CharField(verbose_name=_("name"), max_length=256, blank=True, primary_key=True)
    content = models.BinaryField(verbose_name=_("content"))

    @property
    def file(self):
        return DummyFileDescriptor(self)

    def dump(self, include_hidden=False, include_pk=True):
        field = self._meta.get_field('content')
        return field.get_prep_value(self.content)

    def load(self, data):
        field = self._meta.get_field('content')
        self.content = field.to_python(data)

    @classmethod
    def _get_instance(cls, transaction, pk):
        obj = cls(pk=pk)
        obj._transaction = transaction
        try:
            content = transaction.get_blob(obj.path)
        except GitError:
            raise cls.DoesNotExist(
                'object with pk {} does not exist'.format(pk))
        obj.load(content)
        return obj


class FileSystemDescriptor(DjangoFile):

    def open(self, mode='rb'):
        return super(FileSystemDescriptor, self).open(mode)

class FileSystemModel(git_models.Model, FileModelMixin):
    name = models.CharField(verbose_name=_("name"), max_length=256, blank=True, primary_key=True)

    @property
    def file(self):
        if 'file' not in self.__dict__ or \
                self.__dict__['file'] is None or \
                not isinstance(self.__dict__['file'], FileSystemDescriptor):
            self.__dict__['file'] = FileSystemDescriptor(None, name=self.name)
        return self.__dict__['file']

    @classmethod
    def _get_existing_primary_keys(cls, transaction):
        return []

    @classmethod
    def _get_instance(cls, transaction, pk):
        obj = cls(pk=pk)
        obj._transaction = transaction
        if not os.path.exists(pk):
            raise cls.DoesNotExist(
                'object with pk {} does not exist'.format(pk))
        return obj

    def save(self, *args, **kwargs):
        return
