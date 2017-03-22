from django.contrib import admin

from .models import ssid,vendor,device_ip,auth_server


class SsidAdmin(admin.ModelAdmin):
    fields = ('name', 'status', 'wlan_id', 'vendor', 'ip','web')
    list_display = ('name', 'web.name','ip.name','status','vendor')
    #search_fields = ('name', 'web', 'ip', 'vendor', 'group', 'ap_mac')


admin.site.register(ssid, SsidAdmin)
admin.site.register([vendor,device_ip,auth_server])
