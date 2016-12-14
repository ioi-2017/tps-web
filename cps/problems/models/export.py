from django.conf import settings
from django.db import models

from file_repository.models import FileModel
from tasks.models import Task, State
from trader import get_exporter

from django.utils.translation import ugettext_lazy as _

from trader.exporters import AVAILABLE_EXPORTERS

EXPORTER_CHOICES = [(name, name) for loader, name in AVAILABLE_EXPORTERS]


class ExportPackage(models.Model):

    EXPORT_FORMAT_CHOICES = (
        ("zip", "zip"),
        ("tar", "tar"),
    )
    models.AutoField
    problem = models.ForeignKey("Problem", related_name='exports')
    revision = models.ForeignKey("ProblemRevision", related_name='+')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("creator"))
    creation_date = models.DateTimeField(auto_now_add=True)
    exporter = models.CharField(max_length=20, choices=EXPORTER_CHOICES, verbose_name=_("exporter"))
    export_format = models.CharField(max_length=20, choices=EXPORT_FORMAT_CHOICES, verbose_name=_("export format"), default="zip")
    archive = models.ForeignKey(FileModel, verbose_name=_("archive"), null=True, editable=False)

    def create_archive(self):
        exporter_class = get_exporter(self.exporter)
        with exporter_class(self.revision) as exporter_obj:
            exporter_obj.do_export()
            self.archive = exporter_obj.extract_archive_to_storage(
                self.revision.problem_data.code_name,
                format=self.export_format
            )
            self.save()

    @property
    def is_ready(self):
        return self.archive is not None

    @property
    def being_created(self):
        return self.export_tasks.exclude(state=State.finished.name).exclude(state__isnull=True).exists()


class ExportPackageCreationTask(Task):

    request = models.ForeignKey(ExportPackage, related_name="export_tasks")

    def run(self):
        self.request.create_archive()
