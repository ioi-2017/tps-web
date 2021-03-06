# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-30 07:14
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0003_auto_20160727_2022'),
    ]

    operations = [
        migrations.AddField(
            model_name='problemdata',
            name='memory_limit',
            field=models.IntegerField(default=256, help_text='in megabytes', verbose_name='memory limit'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='problemdata',
            name='time_limit',
            field=models.FloatField(default=1, help_text='in seconds', verbose_name='time limt'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='problemdata',
            name='checker',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='problems.SourceFile', verbose_name='checker'),
        ),
        migrations.AlterField(
            model_name='problemdata',
            name='problem',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='problem_data', to='problems.ProblemRevision'),
        ),
        migrations.AlterField(
            model_name='problemdata',
            name='score_type',
            field=models.CharField(max_length=150, null=True, verbose_name='score type'),
        ),
        migrations.AlterField(
            model_name='problemdata',
            name='score_type_parameters',
            field=models.TextField(null=True, verbose_name='score type parameters'),
        ),
        migrations.AlterField(
            model_name='problemdata',
            name='task_type',
            field=models.CharField(max_length=150, null=True, verbose_name='task type'),
        ),
        migrations.AlterField(
            model_name='problemdata',
            name='task_type_parameters',
            field=models.TextField(null=True, verbose_name='task type parameters'),
        ),
    ]
