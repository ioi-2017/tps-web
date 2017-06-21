from django.utils.translation import ugettext_lazy as _

from git_orm import transaction
from git_orm import models


class GitFile(models.Model):
    name = models.TextField(verbose_name=_("name"), primary_key=True)
    content = models.TextField(verbose_name=_("content"))

    def dump(self, include_hidden=False, include_pk=True):
        field = self._meta.get_field('content')
        return field.get_prep_value()

    def load(self, data):
        field = self._meta.get_field('content')
        self.content = field.to_python(data)

    def delete(self):
        raise NotImplementedError()

    def __str__(self):
        return self.name
