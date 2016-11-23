from django.shortcuts import render,redirect
from django.utils.baseconv import base56
from random import randint
from .models import Img
from django import forms
from django.db.models import F
from PIL import Image
from django.views.generic import DetailView
from datetime import datetime


def random_key():
    return base56.encode(randint(0, 0x7fffff))

class ImgForm(forms.ModelForm):
   class Meta:
       model=Img
       fields=('img','desc')


def index(request):
    if request.method == 'GET':
        latest=Img.objects.order_by('-upload_date')[:12]
        return render(request, 'index.html',{'form':ImgForm(),'latest':latest})
    elif request.method=='POST':
        form=ImgForm(request.POST, request.FILES)
        if form.is_valid():
            key = random_key()
            instance=Img(img=request.FILES['img'],desc=request.POST['desc'],key=key,upload_date=datetime.now(),view_date=datetime.now())
            instance.save()
            object = Img.objects.get(key=key)
            return redirect(object)

def popular(request):
    popular=Img.objects.order_by('view_count')[:12]
    return render(request, 'popular.html',{'popular':popular})


def details(request,key):
    a=Img.objects.get(key=key)
    a.view_count = F('view_count') + 1
    a.view_date=datetime.now()
    a.save()
    a.refresh_from_db()
    return render(request,'uploaded.html',{'instance':a})
