from django.utils.translation import ugettext_lazy as _

from git_orm import transaction
from git_orm import models


class GitFile(models.Model):
    name = models.TextField(verbose_name=_("name"), primary_key=True)
    content = models.TextField(verbose_name=_("content"))

    def dumps(self, include_hidden=False, include_pk=True):
        return self.content.dumps()

    def loads(self, data):
        self.content = self.content.loads(data)

    @transaction.wrap()
    def delete(self):
        raise NotImplementedError()

    def __str__(self):
        return self.name
