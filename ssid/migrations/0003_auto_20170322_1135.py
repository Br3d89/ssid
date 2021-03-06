# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-03-22 09:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0008_alter_user_username_max_length'),
        ('ssid', '0002_ssid_wlan_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='auth_server',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=120, unique=True, verbose_name='WEB_SERVER_DNS')),
                ('ip', models.CharField(default='', max_length=120, verbose_name='RADIUS_SERVER_IP')),
            ],
        ),
        migrations.CreateModel(
            name='device_ip',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=120, unique=True, verbose_name='WIFI_DEVICE_IP')),
                ('mac', models.CharField(default='00:00:00:00:00:00', max_length=120, unique=True, verbose_name='MAC_ADDRESS')),
            ],
        ),
        migrations.CreateModel(
            name='vendor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=120, unique=True, verbose_name='SSID_VENDOR')),
            ],
        ),
        migrations.RemoveField(
            model_name='ssid',
            name='radius',
        ),
        migrations.AddField(
            model_name='ssid',
            name='ap_mac',
            field=models.CharField(default='00:00:00:00:00:00', max_length=120, verbose_name='AP_MAC'),
        ),
        migrations.AddField(
            model_name='ssid',
            name='group',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='auth.Group', verbose_name='GROUP_NAME'),
        ),
        migrations.AlterField(
            model_name='ssid',
            name='acl',
            field=models.CharField(blank=True, max_length=120, verbose_name='ACL_ON_DEVICE'),
        ),
        migrations.AlterField(
            model_name='ssid',
            name='ip',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ssid.device_ip'),
        ),
        migrations.AlterField(
            model_name='ssid',
            name='name',
            field=models.CharField(max_length=120, unique=True, verbose_name='SSID_NAME'),
        ),
        migrations.AlterField(
            model_name='ssid',
            name='status',
            field=models.IntegerField(verbose_name='SSID_STATUS'),
        ),
        migrations.AlterField(
            model_name='ssid',
            name='vendor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ssid.vendor'),
        ),
        migrations.AlterField(
            model_name='ssid',
            name='web',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ssid.auth_server'),
        ),
        migrations.AlterField(
            model_name='ssid',
            name='wlan_id',
            field=models.CharField(default='', max_length=120, verbose_name='WLAN_ID'),
        ),
        migrations.AddField(
            model_name='device_ip',
            name='vendor',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='ssid.vendor'),
        ),
    ]
