from django.contrib import admin

from .models import ssid,vendor,device_ip,auth_server


#class ProductAdmin(admin.ModelAdmin):
#    list_display = ('name', 'category__level', 'category')

#admin.site.register(Product, ProductAdmin)


class SsidAdmin(admin.ModelAdmin):
    #Shows fields that can be changed
    fields = ('name', 'wlan_id','ap_mac', 'vendor', 'ip','web','group')
    #Shows fields in admin pannel
    list_display = ('name', 'web','ip','status','vendor')
    #list_filter = ('name','web')
    #search_fields = ('name', 'web', 'ip', 'vendor', 'group', 'ap_mac')
    search_fields = ('name','web__name','vendor__name','ip__name','ap_mac',)

class AuthServerAdmin(admin.ModelAdmin):
    list_display=('name','ip','group__name')

admin.site.register(ssid, SsidAdmin)
admin.site.register(auth_server,AuthServerAdmin)
admin.site.register([vendor,device_ip])
