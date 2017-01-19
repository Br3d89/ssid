from django.db import models

# Create your models here.


class ssid(models.Model):
    name=models.CharField(max_length=120,unique=True)
    status=models.IntegerField()
    vendor=models.CharField(max_length=120)
    ip=models.CharField(max_length=120)
    radius=models.CharField(max_length=120)
    web=models.CharField(max_length=120)
    acl=models.CharField(max_length=120)

    def __str__(self):
        return 'Name:{} Status:{}'.format(self.name, self.status)

