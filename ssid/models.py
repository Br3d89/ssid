from django.db import models
from django.contrib.auth.models import User,Group
from datetime import datetime,timezone

# Create your models here.


class vendor(models.Model):
    name = models.CharField(max_length=120,unique=True, default="")
    def __str__(self):
        return '{}'.format(self.name)



class device_ip(models.Model):
    name=models.CharField(max_length=120,default="",unique=True)
    vendor=models.ForeignKey(vendor,default="")
    mac=models.CharField(max_length=120,default="00:00:00:00:00:00",unique=True,verbose_name="MAC_ADDRESS")
    def __str__(self):
        return '{}'.format(self.name)



class auth_server(models.Model):
    name=models.CharField(max_length=120, default="",unique=True)
    ip=models.CharField(max_length=120,default="", verbose_name="RADIUS_SERVER_IP")
    group = models.ManyToManyField(Group,default="noc", verbose_name="GROUP_NAME")
    def __str__(self):
        return '{}'.format(self.name)
    def __unicode__(self):
        return self.name


class ssid(models.Model):
    name = models.CharField(max_length=120, unique=True, verbose_name="SSID_NAME")
    status = models.IntegerField(verbose_name="SSID_STATUS",default=0)
    vendor = models.ForeignKey(vendor, verbose_name="SSID_VENDOR")
    ip = models.ForeignKey(device_ip, verbose_name="WIFI_DEVICE_IP")
    #radius=models.CharField(max_length=120)
    web = models.ForeignKey(auth_server, verbose_name="AUTH_SERVER")
    acl = models.CharField(max_length=120, blank=True, verbose_name="ACL_ON_DEVICE")
    wlan_id = models.CharField(max_length=120, default="", verbose_name="WLAN_ID")
    ap_mac = models.CharField(max_length=120, default="00:00:00:00:00:00", verbose_name="AP_MAC")
    group = models.ManyToManyField(Group, verbose_name="GROUP_NAME")
    start_date=models.DateTimeField(default=datetime.now)
    end_date=models.DateTimeField(default=datetime.now)

    def __str__(self):
        return 'Name:{} Status:{}'.format(self.name, self.status)

    @property
    def remaining_time(self):
        return (self.end_date-datetime.now(timezone.utc)).strftime("%M:%S")
