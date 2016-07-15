# Amir Keivan Mohtashami

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from problems.models.problem import Problem


class Comment(models.Model):
    problem = models.ForeignKey(Problem, verbose_name=_("problem"))
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("author"))
    text = models.TextField(verbose_name=_("text"))
    posting_date = models.DateTimeField(auto_now_add=True, verbose_name=_("posting date"))