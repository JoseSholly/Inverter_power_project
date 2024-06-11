from django.contrib import admin
from .models import Calculation

class CalculationAdmin(admin.ModelAdmin):
    list_display = ['id', 'created', 'total_load', 'inverter_rating']
    list_filter = ['created', "updated"]
    search_fields = ['id']

admin.site.register(Calculation, CalculationAdmin)
