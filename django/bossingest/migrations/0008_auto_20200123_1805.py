# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2020-01-23 18:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bossingest', '0007_auto_20190627_2236'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingestjob',
            name='status',
            field=models.IntegerField(choices=[(0, 'Preparing'), (1, 'Uploading'), (2, 'Complete'), (3, 'Deleted'), (4, 'Failed'), (5, 'Completing')], default=0),
        ),
    ]
