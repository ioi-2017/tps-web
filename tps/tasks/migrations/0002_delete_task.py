# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2017-04-07 11:10
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0081_auto_20170407_1110'),
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Task',
        ),
    ]