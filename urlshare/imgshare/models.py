from django.db import models
from datetime import datetime
from imagekit.models.fields import ImageSpecField
from imagekit.processors import ResizeToFit, Adjust,ResizeToFill
from django.db.models import F
from django.utils.baseconv import base56
from random import randint
from django.contrib.auth.models import User


class Img(models.Model):
    img=models.ImageField(upload_to='images')
    img_medium=ImageSpecField(source='img',
                                      processors=[ResizeToFill(280, 170)],
                                      format='JPEG',
                                      options={'quality': 90})
    img_big=ImageSpecField(source='img',
                                      processors=[ResizeToFill(640, 480)],
                                      format='JPEG',
                                      options={'quality': 90})
    desc=models.CharField(max_length=120,blank=True)
    key=models.SlugField(unique=True,max_length=10)
    upload_date=models.DateTimeField(default=datetime.now)
    view_date=models.DateTimeField(default=datetime.now)
    view_count=models.PositiveIntegerField(default=0)
    like_count=models.PositiveIntegerField(default=0)
    usr=models.ManyToManyField(User)

    def get_absolute_url(self):
        return "/{}".format(self.key)
    def __str__(self):
        return 'Key:{} Image name:{}'.format(self.key,self.img.name)
    @classmethod
    def create(cls,img,desc,user=0):
        key=base56.encode(randint(0, 0x7fffff))
        obj, _=cls.objects.get_or_create(img=img,
                                         defaults={'key':key,'desc':desc})
        obj.usr.add(user)
        return obj

