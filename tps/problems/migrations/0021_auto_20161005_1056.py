# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-10-05 10:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0020_auto_20161003_0818'),
    ]

    operations = [
        migrations.AddField(
            model_name='solution',
            name='score',
            field=models.FloatField(default=1, verbose_name='score'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='testcase',
            name='_input_generation_parameters',
            field=models.TextField(blank=True, max_length=100, verbose_name='input generation command'),
        ),
        migrations.AlterField(
            model_name='testcase',
            name='_input_uploaded_file',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='file_repository.FileModel', verbose_name='input uploaded file'),
        ),
        migrations.AlterField(
            model_name='testcase',
            name='_output_uploaded_file',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='file_repository.FileModel', verbose_name='output uploaded file'),
        ),
        migrations.AlterField(
            model_name='testcase',
            name='_solution',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='problems.SourceFile', verbose_name='solution'),
        ),
    ]