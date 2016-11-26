from django.shortcuts import render,redirect
from django.utils.baseconv import base56
from random import randint
from .models import Img
from django import forms
from django.db.models import F
from datetime import datetime
from django.contrib import auth


def random_key():
    return base56.encode(randint(0, 0x7fffff))

class ImgForm(forms.ModelForm):
   class Meta:
       model=Img
       fields=('img','desc')


def index(request):
    args={}
    args['form'] = ImgForm()
    args['latest'] =Img.objects.order_by('-upload_date')[:12]
    args['username']= auth.get_user(request).username
    if request.POST:
        form=ImgForm(request.POST, request.FILES)
        if form.is_valid():
            img=form.cleaned_data['img']
            desc=form.cleaned_data['desc']
            #img=request.FILES['img']
            #desc=request.POST['desc']
            instance=Img.create(img,desc)
            return redirect(instance)
        else:
            args['form']=form
    return render(request, 'index.html', args)

def popular(request):
    return render(request, 'popular.html',{'popular':Img.objects.order_by('view_count')[:12],
                                           'username':auth.get_user(request).username})

def toplikes(request):
    return render(request, 'popular.html', {'popular': Img.objects.order_by('-like_count')[:12],
                                            'username': auth.get_user(request).username})


def details(request,key):
    a = Img.objects.get(key=key)
    if request.method == 'GET':
        a.view_count = F('view_count') + 1
        a.view_date=datetime.now()
    elif request.method == 'POST':
        a.like_count = F('like_count') + 1
    a.save()
    a.refresh_from_db()
    return render(request, 'detail.html', {'instance': a,'username':auth.get_user(request).username})

