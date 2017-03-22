from django.contrib import admin

from .models import ssid,vendor,device_ip,auth_server


#class ProductAdmin(admin.ModelAdmin):
#    list_display = ('name', 'category__level', 'category')

#admin.site.register(Product, ProductAdmin)


class SsidAdmin(admin.ModelAdmin):
    fields = ('name', 'wlan_id','ap_mac', 'vendor', 'ip','web','group')
    list_display = ('name', 'web','ip','status','vendor','group')
    #list_filter = ('name','web')
    #search_fields = ('name', 'web', 'ip', 'vendor', 'group', 'ap_mac')
    search_fields = ('web__name',)


admin.site.register(ssid, SsidAdmin)
admin.site.register([vendor,device_ip,auth_server])
