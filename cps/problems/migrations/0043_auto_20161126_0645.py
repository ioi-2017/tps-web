# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-11-26 06:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0042_auto_20161125_1007_squashed_0048_auto_20161125_1832'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problemfork',
            name='head',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='problem_fork', to='problems.ProblemRevision', verbose_name='head'),
        ),
    ]