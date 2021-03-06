# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-12-04 00:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bosscore', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='channel',
            old_name='default_time_step',
            new_name='default_time_sample',
        ),
        migrations.RemoveField(
            model_name='experiment',
            name='max_time_sample',
        ),
        migrations.AddField(
            model_name='experiment',
            name='num_time_samples',
            field=models.IntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='coordinateframe',
            name='time_step',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='coordinateframe',
            name='time_step_unit',
            field=models.CharField(blank=True, choices=[('nanoseconds', 'NANOSECONDS'), ('microseconds', 'MICROSECONDS'), ('milliseconds', 'MILLISECONDS'), ('seconds', 'SECONDS')], max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='experiment',
            name='num_hierarchy_levels',
            field=models.IntegerField(default=1),
        ),
    ]
