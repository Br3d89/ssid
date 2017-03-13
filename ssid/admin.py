from django.contrib import admin

from .models import ssid


class SsidAdmin(admin.ModelAdmin):
    fields = ('name', 'status', 'vendor', 'ip','web')


admin.site.register(ssid, SsidAdmin)

