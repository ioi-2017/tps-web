import logging

from django.conf import settings
from django.db import models

from file_repository.models import FileModel
from tasks.tasks import CeleryTask
from trader import get_exporter

from django.utils.translation import ugettext_lazy as _

from trader.exporters import AVAILABLE_EXPORTERS

EXPORTER_CHOICES = [(name, name) for loader, name in AVAILABLE_EXPORTERS]

logger = logging.getLogger(__name__)

class ExportPackage(models.Model):

    EXPORT_FORMAT_CHOICES = (
        ("zip", "zip"),
        ("tar", "tar"),
    )
    problem = models.ForeignKey("Problem", related_name='exports')
    revision = models.ForeignKey("ProblemRevision", related_name='+')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("creator"))
    creation_date = models.DateTimeField(auto_now_add=True)
    exporter = models.CharField(max_length=20, choices=EXPORTER_CHOICES, verbose_name=_("exporter"))
    export_format = models.CharField(max_length=20, choices=EXPORT_FORMAT_CHOICES, verbose_name=_("export format"), default="zip")
    archive = models.ForeignKey(FileModel, verbose_name=_("archive"), null=True, editable=False)

    def _create_archive(self):
        exporter_class = get_exporter(self.exporter)
        with exporter_class(self.revision) as exporter_obj:
            exporter_obj.do_export()
            self.archive = exporter_obj.extract_archive_to_storage(
                self.revision.problem_data.code_name,
                format=self.export_format
            )
            self.save()

    def create_archive(self):
        if self.creation_task_id is not None:
            self.creation_task_id = ExportPackageCreationTask().delay(self).id
            self.save()

    @property
    def is_ready(self):
        return self.archive is not None

    @property
    def being_created(self):
        return not self.is_ready and self.creation_task_id is not None


class ExportPackageCreationTask(CeleryTask):

    def validate_dependencies(self, request):
        result = True
        for testcase in request.revision.testcase_set.all():
            if not testcase.testcase_generation_completed():
                logger.info("Waiting until testcase {} is generated".format(str(testcase)))
                testcase.generate()
                result = None
        return result

    def execute(self, request):
        request._create_archive()
