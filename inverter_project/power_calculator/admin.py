from typing import ClassVar

from django.contrib import admin

from .models import Appliance


@admin.register(Appliance)
class ApplianceAdmin(admin.ModelAdmin):
    list_display: ClassVar[list[str]] = ["id", "name", "created"]
    search_fields: ClassVar[list[str]] = ["name"]
