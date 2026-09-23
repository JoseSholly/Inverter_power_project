from django.contrib import admin

from .models import Appliance


@admin.register(Appliance)
class ApplianceAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "created"]
    search_fields = ["name"]
