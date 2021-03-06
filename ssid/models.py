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
    auth_scheme = models.ManyToManyField(auth_scheme, blank=True,default="", verbose_name="AUTH_SCHEME")
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

def test_func():
    return "acl_test"

class ssid(models.Model):
    def acl_on_device(self):
        pass

    #def test_func(self):
    #    return "test"
        #if self.ip=='10.1.29.10':
        #    print('First hook from models')
        #    self.acl="inet2,inet3"
        #else:
        #    self.acl = ""

    name = models.CharField(max_length=120, unique=True, verbose_name="SSID_NAME")
    status = models.IntegerField(verbose_name="SSID_STATUS",default=0)
    vendor = models.ForeignKey(vendor, verbose_name="SSID_VENDOR")
    ip = models.ForeignKey(device_ip, verbose_name="WIFI_DEVICE_IP")
    #radius=models.CharField(max_length=120)
    web = models.ForeignKey(auth_server, verbose_name="AUTH_SERVER")
    acl = models.CharField(max_length=120, blank=True, verbose_name="ACL_ON_DEVICE")
    wlan_id = models.CharField(max_length=120, default="" , verbose_name="WLAN_ID")
    ap_mac = models.CharField(max_length=120, default="00:00:00:00:00:00", verbose_name="AP_MAC")
    group = models.ManyToManyField(Group, verbose_name="GROUP_NAME")
    start_date=models.DateTimeField(default=datetime.now)
    end_date=models.DateTimeField(default=datetime.now)
    auth_scheme = models.ForeignKey(auth_scheme, blank=True, default="",verbose_name="AUTH_SCHEME")
    #test_field = models.CharField(max_length=120,default=test_func)

    def __str__(self):
        return 'Name:{} Status:{}'.format(self.name, self.status)

    @property
    def remaining_time(self):
        return str((self.end_date-datetime.now(timezone.utc)).total_seconds()).split(".")[0]

    #@property
    def ip_for_vendor(self):
        return "\n".join([p for p in list(device_ip.objects.values_list('name', flat=True).filter(vendor__name=self.vendor))])


    @classmethod
    def create(cls, name, vendor, ip, web, wlan_id, group, auth_scheme):
        print('We are creating ssid')
        obj=cls(name=name,vendor=vendor,ip=ip,web=web,wlan_id=wlan_id,group=group,auth_scheme=auth_scheme)
        #obj, _ = cls.objects.get_or_create(name='bred_create_method_nameaaaad', vendor=vendor, ip=ip, web=web,wlan_id=wlan_id, ap_mac=ap_mac, group=group, auth_scheme=auth_scheme)
        return obj



