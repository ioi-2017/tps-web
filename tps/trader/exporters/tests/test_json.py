from django.test import TestCase

from trader.exporters import JSONExporter
from trader.exporters.tests import ExporterBaseTestCase


class JSONExporterTestCase(ExporterBaseTestCase, TestCase):
    def do_export(self):
        with JSONExporter(self.problem) as exporter:
            exporter.do_export()
            return exporter.extract_archive_to_storage("test_problem")
