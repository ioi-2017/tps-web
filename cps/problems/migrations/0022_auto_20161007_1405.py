# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-10-07 14:05
from __future__ import unicode_literals

from django.db import migrations, models
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0021_auto_20161005_1056'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='solution',
            name='score',
        ),
        migrations.AddField(
            model_name='solution',
            name='should_be_present_verdicts',
            field=multiselectfield.db.fields.MultiSelectField(choices=[('1', 'Accept'), ('2', 'Wrong Answer'), ('3', 'Time Limit'), ('4', 'Memory Limit'), ('5', 'Presentation Error')], max_length=9, null=True),
        ),
        migrations.AddField(
            model_name='solution',
            name='should_not_be_present_verdicts',
            field=multiselectfield.db.fields.MultiSelectField(choices=[('1', 'Accept'), ('2', 'Wrong Answer'), ('3', 'Time Limit'), ('4', 'Memory Limit'), ('5', 'Presentation Error')], max_length=9, null=True),
        ),
        migrations.AlterField(
            model_name='testcase',
            name='name',
            field=models.CharField(blank=True, max_length=20, verbose_name='name'),
        ),
    ]
