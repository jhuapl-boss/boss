# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2017-03-03 23:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BlogPost',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=48)),
                ('message', models.TextField()),
                ('post_on', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='SystemNotice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('alert-success', 'Success (green)'), ('alert-info', 'Info (blue)'), ('alert-warning', 'Warning (yellow)'), ('alert-danger', 'Danger (red)')], max_length=100)),
                ('heading', models.CharField(max_length=48)),
                ('message', models.CharField(max_length=1024)),
                ('show_on', models.DateTimeField()),
                ('hide_on', models.DateTimeField()),
            ],
        ),
    ]
