from django.db import models
from datetime import datetime
from imagekit.models.fields import ImageSpecField
from imagekit.processors import ResizeToFit, Adjust,ResizeToFill


class Img(models.Model):
    img=models.ImageField(upload_to='images')
    img_medium=ImageSpecField([Adjust(contrast=1.2, sharpness=1.1),ResizeToFit(300, 200)],source='img',format='JPEG', options={'quality': 90})
    desc=models.CharField(max_length=120,blank=True)
    key=models.SlugField(unique=True,max_length=10)
    upload_date=models.DateTimeField()
    view_date=models.DateTimeField()
    view_count=models.PositiveIntegerField(default=0)

    def get_absolute_url(self):
        from django.urls import reverse
        return "/{}".format(self.key)
        #return reverse('imgshare.views.details', args=[str(self.key)])
    def __str__(self):
        return 'Key:{} Image name:{}'.format(self.key,self.img.name)