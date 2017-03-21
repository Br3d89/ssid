from django.contrib import admin
from django.contrib.auth.models import User

from .models import ssid


class SsidAdmin(admin.ModelAdmin):
    fields = ('name', 'status', 'wlan_id', 'vendor', 'ip','web')
    list_display = ('name', 'web','ip','status','vendor')
    search_fields = ('name','web','ip','vendor')


admin.site.register(ssid, SsidAdmin)
