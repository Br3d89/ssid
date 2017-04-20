from django.db import models
from django.contrib.auth.models import User,Group
from datetime import datetime,timezone


class auth_scheme(models.Model):
    name = models.CharField(max_length=120, default="")
    desc=models.TextField(default="", blank=True,)
    def __str__(self):
        return '{}'.format(self.name)

    class Meta:
        verbose_name = 'Auth scheme'
        verbose_name_plural = 'Auth schemes'


class vendor(models.Model):
    name = models.CharField(max_length=120,unique=True, default="")
    auth_scheme = models.ManyToManyField(auth_scheme, null=True, blank=True, verbose_name="AUTH_SCHEME")
    def __str__(self):
        return '{}'.format(self.name)



class device_ip(models.Model):
    name=models.CharField(max_length=120,default="",unique=True)
    vendor=models.ForeignKey(vendor,default="")
    mac=models.CharField(max_length=120,default="00:00:00:00:00:00",unique=True,verbose_name="MAC_ADDRESS")
    hostname=models.CharField(max_length=120,default="",verbose_name="HOSTNAME")
    def __str__(self):
        return '{}'.format(self.name)

    class Meta:
        verbose_name = 'Wi-Fi device'
        verbose_name_plural = 'Wi-Fi devices'



class auth_server(models.Model):
    name=models.CharField(max_length=120, default="",unique=True)
    ip=models.CharField(max_length=120,default="", verbose_name="RADIUS_SERVER_IP")
    group = models.ManyToManyField(Group,default="noc", verbose_name="GROUP_NAME")
    def __str__(self):
        return '{}'.format(self.name)
    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Auth server'
        verbose_name_plural = 'Auth servers'


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
    auth_scheme = models.ForeignKey(auth_scheme, null=True, blank=True,verbose_name="AUTH_SCHEME")

    def __str__(self):
        return 'Name:{} Status:{}'.format(self.name, self.status)

    @property
    def remaining_time(self):
        return str((self.end_date-datetime.now(timezone.utc)).total_seconds()).split(".")[0]

    #@property
    #def ip_for_vendor(self):
    #    return "\n".join([p for p in list(device_ip.objects.values_list('name', flat=True).filter(vendor__name=self.vendor))])

'''
    @classmethod
    def create(cls, img, desc, user=0):
        obj, _ = cls.objects.get_or_create(img=img,
                                           defaults={'key': key, 'desc': desc})
        obj.usr.add(user)
        return obj
'''