from django.contrib import admin
from .models import Calculation

class CalculationAdmin(admin.ModelAdmin):
    list_display = ['id', 'created', 'total_power_needed', 'inverter_power']
    list_filter = ['created', "updated"]
    search_fields = ['id']

admin.site.register(Calculation, CalculationAdmin)
