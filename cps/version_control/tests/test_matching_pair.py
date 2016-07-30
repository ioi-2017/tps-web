# Amir Keivan Mohtashami

from django.test import TestCase
from version_control.tests.models import DummyRevision, DummyModel1


class MatchingPairsTestCase(TestCase):

    def setUp(self):
        DummyRevision.objects.create(uid="dummy1")
        DummyRevision.objects.create(uid="dummy2")

    def test_finding_matched_pairs(self):
        revision1 = DummyRevision.objects.get(uid="dummy1")
        revision2 = DummyRevision.objects.get(uid="dummy2")
        dummy1 = DummyModel1(name="test", revision=revision1)
        dummy2 = DummyModel1(name="test", revision=revision2)
        dummy1.save()
        dummy2.save()
        self.assertTrue((dummy1, dummy2) in revision1.find_matching_pairs(revision2))

    def test_not_matching_irrelevant_objects(self):
        revision1 = DummyRevision.objects.get(uid="dummy1")
        revision2 = DummyRevision.objects.get(uid="dummy2")
        dummy1 = DummyModel1(name="test", revision=revision1)
        dummy2 = DummyModel1(name="test2", revision=revision2)
        dummy1.save()
        dummy2.save()
        self.assertFalse((dummy1, dummy2) in revision1.find_matching_pairs(revision2))

    def test_removed_object_pair(self):
        revision1 = DummyRevision.objects.get(uid="dummy1")
        revision2 = DummyRevision.objects.get(uid="dummy2")
        dummy1 = DummyModel1(name="test", revision=revision1)
        dummy1.save()
        self.assertTrue((dummy1, None) in revision1.find_matching_pairs(revision2))

    def test_added_object_pair(self):
        revision1 = DummyRevision.objects.get(uid="dummy1")
        revision2 = DummyRevision.objects.get(uid="dummy2")
        dummy2 = DummyModel1(name="test2", revision=revision2)
        dummy2.save()
        self.assertTrue((None, dummy2) in revision1.find_matching_pairs(revision2))