# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-03-23 11:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0008_alter_user_username_max_length'),
        ('ssid', '0005_auto_20170322_1653'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ssid',
            name='group',
        ),
        migrations.AddField(
            model_name='ssid',
            name='group',
            field=models.ManyToManyField(to='auth.Group', verbose_name='GROUP_NAME'),
        ),
    ]
