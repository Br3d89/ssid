"""ssidswitcher URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from ssid.views import index,detail,ssid_status,ssid_update,ssid_error,login,logout,ssid_busy,profile,ssid_add

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^ssid_add/', ssid_add),
    url(r'ssid_update/',ssid_update),
    url(r'^ssid/(.*)', detail),
    url(r'^ssid_status/', ssid_status),
    url(r'^ssid_busy/', ssid_busy),
    url(r'^ssid_error/', ssid_error),
    url(r'^auth/login/',login),
    url(r'^profile', profile),
    url(r'^auth/logout/', logout),
    url(r'^', index)
]
