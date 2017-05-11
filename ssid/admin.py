from django.contrib import admin
from django import forms

from .models import ssid,vendor,device_ip,auth_server,auth_scheme


#class ProductAdmin(admin.ModelAdmin):
#    list_display = ('name', 'category__level', 'category')

#admin.site.register(Product, ProductAdmin)
def group_func(obj):
    return "\n".join([p.name for p in obj.group.all()])


class CustomUserAdminForm(forms.ModelForm):
    ip_for_vendor = forms.CharField()
#
    #class Meta:
    #    model = ssid

def make_enabled(modeladmin,request,queryset):
    queryset.update(status="1")

def make_disabled(modeladmin,request,queryset):
    queryset.update(status="0")

def push_to_device(modeladmin,request,queryset):
    for obj in queryset:
        if str(obj.vendor)=='cisco':
            print('Cisco')
        else:
            print(obj.vendor)



make_enabled.short_description = "Mark selected ssids as enabled"
make_disabled.short_description = "Mark selected ssids as disabled"


class SsidAdmin(admin.ModelAdmin):
    #def ip_for_vendor(self, obj):
    #    return 'the_key'

    #Shows fields that can be changed
    #readonly_fields = ('ip_for_vendor',)
    fields = ('name', 'wlan_id','ap_mac', 'vendor', 'ip','web','group','auth_scheme')
    #fieldsets=('name', 'wlan_id', 'ap_mac', 'vendor', ('ip_for_vendor', 'web'), 'group', 'auth_scheme')
    #Shows fields in admin pannel
    group_func.short_description = 'SSID_GROUP'
    list_display = ('name', 'web','ip','status','vendor',group_func,'auth_scheme','test_field')
    #list_filter = ('name','web')
    #search_fields = ('name', 'web', 'ip', 'vendor', 'group', 'ap_mac')
    search_fields = ('name','web__name','vendor__name','ip__name','ap_mac','auth_scheme__name')
    actions = [make_enabled,make_disabled,push_to_device]

    def get_changeform_initial_data(self, request):
        return {'name': self.test_aaa()}

    def test_aaa(self):
        return 'olololo'
    #def ssid_group(self, obj):
    #    return "\n".join([p.name for p in obj.group.all()])

    #def ip_for_vendor(self,obj):
    #    return "\n".join([ p for p in list(device_ip.objects.values_list('name', flat=True).filter(vendor__name=obj.vendor))])
       #return "\n".join([p.name for p in obj.group.all()])


class AuthServerAdmin(admin.ModelAdmin):
    group_func.short_description = 'SERVER_GROUP'
    list_display=('name','ip',group_func)



class NetworkDeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor', 'mac','hostname')


class AuthSchemeAdmin(admin.ModelAdmin):
    list_display = ('name', 'desc')


class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'auth_scheme_list')

    def auth_scheme_list(self, obj):
        return "\n".join([p.name for p in obj.auth_scheme.all()])


admin.site.register(ssid, SsidAdmin)
admin.site.register(auth_server,AuthServerAdmin)
admin.site.register(device_ip, NetworkDeviceAdmin)
admin.site.register(auth_scheme,AuthSchemeAdmin)
admin.site.register(vendor,VendorAdmin)
#admin.site.register([vendor,])
