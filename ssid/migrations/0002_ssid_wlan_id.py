# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-27 14:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ssid', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ssid',
            name='wlan_id',
            field=models.CharField(default='', max_length=120),
        ),
    ]
