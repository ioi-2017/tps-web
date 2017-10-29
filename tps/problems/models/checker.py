from django.db import models

from problems.models.file import SourceFile

__all__ = ["Checker"]


class Checker(SourceFile):
    class Meta:
        storage_name = "checker"
