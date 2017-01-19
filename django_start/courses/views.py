from django.shortcuts import render,redirect
# Create your views here.f
from django import forms
from .models import Student

def is_valid_email(val):
    if val.endswith('.ru'):
        raise forms.ValidationError('.ru domain is not allowed!')


#class StudentForm(forms.Form):
#    name=forms.CharField(required=True)
#    birthdate=forms.DateField()
#    email=forms.EmailField(validators=[is_valid_email])

class StudentForm(forms.ModelForm):
    email = forms.EmailField(validators=[is_valid_email])
    class Meta:
        model=Student
        fields=('name','birthdate','email')


def index(request):
    form=StudentForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('/')
    return render(request,'index.html',{'form':form})




