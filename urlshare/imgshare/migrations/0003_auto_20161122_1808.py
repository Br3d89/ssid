# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-22 16:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('imgshare', '0002_auto_20161122_1804'),
    ]

    operations = [
        migrations.AlterField(
            model_name='img',
            name='view_date',
            field=models.DateTimeField(default='2016-11-22 18:08:41'),
        ),
    ]
