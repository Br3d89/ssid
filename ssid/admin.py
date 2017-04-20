from django.contrib import admin

from .models import ssid,vendor,device_ip,auth_server,auth_scheme


#class ProductAdmin(admin.ModelAdmin):
#    list_display = ('name', 'category__level', 'category')

#admin.site.register(Product, ProductAdmin)


class SsidAdmin(admin.ModelAdmin):
    #Shows fields that can be changed
    fields = ('name', 'wlan_id','ap_mac', 'vendor', 'ip','web','group','auth_scheme')
    #Shows fields in admin pannel
    list_display = ('name', 'web','ip','status','vendor','ssid_group','auth_scheme')
    #list_filter = ('name','web')
    #search_fields = ('name', 'web', 'ip', 'vendor', 'group', 'ap_mac')
    search_fields = ('name','web__name','vendor__name','ip__name','ap_mac','auth_scheme__name')

    def ssid_group(self, obj):
        return "\n".join([p.name for p in obj.group.all()])


class AuthServerAdmin(admin.ModelAdmin):
    list_display=('name','ip','server_group')

    def server_group(self, obj):
        return "\n".join([p.name for p in obj.group.all()])


class NetworkDeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor', 'mac')


admin.site.register(ssid, SsidAdmin)
admin.site.register(auth_server,AuthServerAdmin)
admin.site.register(device_ip, NetworkDeviceAdmin)
admin.site.register([vendor,auth_scheme])
