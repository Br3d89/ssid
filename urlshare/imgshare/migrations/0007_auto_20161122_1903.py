# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-22 17:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('imgshare', '0006_auto_20161122_1856'),
    ]

    operations = [
        migrations.AlterField(
            model_name='img',
            name='img',
            field=models.ImageField(upload_to='images'),
        ),
        migrations.AlterField(
            model_name='img',
            name='view_date',
            field=models.DateTimeField(default='2016-11-22 19:03:06'),
        ),
    ]
