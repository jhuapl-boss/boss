# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('collection_name', models.CharField(max_length=255, primary_key=True, verbose_name='Name of the Collection', serialize=False)),
                ('collection_description', models.CharField(max_length=4096, blank=True)),
            ],
            options={
                'db_table': 'collections',
            },
        ),
        migrations.CreateModel(
            name='Experiment',
            fields=[
                ('experiment_name', models.CharField(max_length=255, primary_key=True, verbose_name='Name of the Experiment', serialize=False)),
                ('experiment_description', models.CharField(max_length=4096, blank=True)),
                ('num_resolution_levels', models.IntegerField(default=0)),
                ('heirarchy_method', models.CharField(choices=[(0, 'near_iso'), (1, 'iso'), (2, 'slice')], max_length=100)),
                ('collection', models.ForeignKey(to='bossmeta.Collection')),
            ],
            options={
                'db_table': 'experiments',
            },
        ),
    ]
