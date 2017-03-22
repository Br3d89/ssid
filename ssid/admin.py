from django.contrib import admin

from .models import ssid,vendor,device_ip,auth_server


class SsidAdmin(admin.ModelAdmin):
    fields = ('name', 'status', 'wlan_id', 'vendor_id', 'ip_id','web_id')
    list_display = ('name', 'web.name','ip.name','status','vendor')


admin.site.register(ssid, SsidAdmin)
admin.site.register([vendor,device_ip,auth_server])
