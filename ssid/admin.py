from django.contrib import admin
from django.contrib.auth.models import User

from .models import ssid,vendor,device_ip,auth_server


class SsidAdmin(admin.ModelAdmin):
    fields = ('name', 'status', 'wlan_id', 'vendor', 'ip','web','group','ap_mac')
    list_display = ('name', 'web','ip','status','vendor','group')
    search_fields = ('name','web','ip','vendor','group','ap_mac')


admin.site.register(ssid, SsidAdmin)
admin.site.register([vendor,device_ip,auth_server])