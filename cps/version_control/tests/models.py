from django.db import models

from version_control.models import VersionModel

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
