from django.shortcuts import render,redirect
from django.contrib import auth
from django.contrib.auth.forms import UserCreationForm
from imgshare.models import Img
from imgshare.views import ImgForm


def login(request):
    args={}
    if request.POST:
        username=request.POST.get('username')
        password=request.POST.get('password')
        user=auth.authenticate(username=username,password=password)
        if user is not None:
            auth.login(request,user)
            return redirect('/')
        else:
            args['login_error']='Пользователь не найден'
            return render(request,'login.html', args)
    else:
        return render(request, 'login.html', args)
def logout(request):
    auth.logout(request)
    return redirect('/')

def register(request):
    args={}
    args['form']=UserCreationForm()
    if request.POST:
        newuser_form=UserCreationForm(request.POST)
        if newuser_form.is_valid():
            newuser_form.save()
            newuser=auth.authenticate(username=newuser_form.cleaned_data['username'],password=newuser_form.cleaned_data['password2'])
            auth.login(request,newuser)
            return redirect('/')
        else:
            args['form']=newuser_form
    return render(request,'register.html',args)

def profile(request):
    args={}
    args['form']=ImgForm()
    args['username'] = auth.get_user(request).username
    a=Img.objects.all()
    user_id=request.user.id
    #image_id=Img.usr.through.objects.filter(user_id=user_id)
    images_id=Img.usr.through.objects.values_list('img_id', flat=True).filter(user_id=user_id)
    list=[]
    for i in images_id:
        list.append(Img.objects.filter(id=i)[0])
    args['latest']=list
    return render(request,'profile.html',args)



