from django.db import models
from django.contrib.auth.models import User,Group

# Create your models here.


class vendor(models.Model):
    name = models.CharField(max_length=120,unique=True, default="",verbose_name="SSID_VENDOR")
    def __str__(self):
        return '{}'.format(self.name)


class device_ip(models.Model):
    name=models.CharField(max_length=120,default="",unique=True, verbose_name="WIFI_DEVICE_IP")
    vendor=models.ForeignKey(vendor,default="")
    mac=models.CharField(max_length=120,default="00:00:00:00:00:00",unique=True,verbose_name="MAC_ADDRESS")
    def __str__(self):
        return '{}'.format(self.name)


class auth_server(models.Model):
    name=models.CharField(max_length=120, default="",unique=True,verbose_name="WEB_SERVER_DNS")
    ip=models.CharField(max_length=120,default="", verbose_name="RADIUS_SERVER_IP")
    def __str__(self):
        return '{}'.format(self.name)


class ssid(models.Model):
    name = models.CharField(max_length=120, unique=True, verbose_name="SSID_NAME")
    status = models.IntegerField(verbose_name="SSID_STATUS",default=0)
    vendor = models.ForeignKey(vendor)
    ip = models.ForeignKey(device_ip)
    #radius=models.CharField(max_length=120)
    web = models.ForeignKey(auth_server)
    acl = models.CharField(max_length=120, blank=True, verbose_name="ACL_ON_DEVICE")
    wlan_id = models.CharField(max_length=120, default="", verbose_name="WLAN_ID")
    ap_mac = models.CharField(max_length=120, default="00:00:00:00:00:00", verbose_name="AP_MAC")
    group = models.ForeignKey(Group, default=1, verbose_name="GROUP_NAME")

    def __str__(self):
        return 'Name:{} Status:{}'.format(self.name, self.status)

