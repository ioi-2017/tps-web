from django.db import models
from django.utils.translation import ugettext_lazy as _


class Invocation(models.Model):
    problem = models.ForeignKey("ProblemRevision", verbose_name=_("problem"))
    creation_date = models.DateTimeField(auto_now_add=True, verbose_name=_("creation date"))
