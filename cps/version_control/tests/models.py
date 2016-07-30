# Amir Keivan Mohtashami

from django.db import models
from version_control.models import Revision, VersionModel


class DummyRevision(Revision):

    parent_revision = models.ForeignKey("DummyRevision", null=True)
    depth = models.IntegerField()
    uid = models.CharField(max_length=100)

    def get_related_objects(self):
        return self.dummies.all()


class DummyModel1(VersionModel):
    revision = models.ForeignKey(DummyRevision, related_name='dummies')
    name = models.CharField(max_length=100)

    def matches(self, another_version):
        return self.name == another_version.name

class Question(VersionModel):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')


class Choice(VersionModel):
    question = models.ForeignKey(Question)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

class Person(VersionModel):
    questions = models.ManyToManyField(Question)

class Student(VersionModel):
    name = models.CharField(max_length=128)

class Group(VersionModel):
    name = models.CharField(max_length=128)
    members = models.ManyToManyField(Student, through='Membership')

class Membership(VersionModel):
    student = models.ForeignKey(Student)
    group = models.ForeignKey(Group)

class A(VersionModel):
    b = models.ManyToManyField('B')

class B(VersionModel):
    c = models.ManyToManyField('C')

class C(VersionModel):
    a = models.ManyToManyField('A')
