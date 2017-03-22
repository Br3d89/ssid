from django.contrib import admin

from .models import ssid,vendor,device_ip,auth_server


#class ProductAdmin(admin.ModelAdmin):
#    list_display = ('name', 'category__level', 'category')

#admin.site.register(Product, ProductAdmin)


class SsidAdmin(admin.ModelAdmin):
    fields = ('name', 'status', 'wlan_id', 'vendor', 'ip','web')
    list_display = ('name', 'web','ip','status','vendor')
    #search_fields = ('name', 'web', 'ip', 'vendor', 'group', 'ap_mac')


#admin.site.register(ssid, SsidAdmin)
admin.site.register([ssid,vendor,device_ip,auth_server],SsidAdmin)
