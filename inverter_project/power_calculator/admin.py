from django.contrib import admin
from .models import Calculation, Appliance, CalculationItem

class CalculationItemInline(admin.TabularInline):
    model = CalculationItem
    raw_id_fields = ['appliance']
    fields = ['appliance', 'quantity', 'power_rating']
    extra = 1

class CalculationAdmin(admin.ModelAdmin):
    list_display = ['id',
                     'total_load',
                    'inverter_rating',
                    'backup_time',
                    'battery_capacity',
                    'total_battery_capacity',
                    'numbers_of_batteries',
                    'total_solar_panel_capacity_needed',
                    'numbers_of_solar_panel',
                    'total_current',
                    'created',
                    ]
    readonly_fields= [
        'total_load',
        'inverter_rating',
        'total_battery_capacity',
        'numbers_of_batteries',
        'total_solar_panel_capacity_needed',
        'numbers_of_solar_panel',
        'total_current',
    ]
    search_fields = ['id']
    inlines = [CalculationItemInline]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.calculate_total_load()
        form.instance.calculate_total_inverter_rating()
        form.instance.calculate_total_battery_capacity()
        form.instance.calculate_no_of_battery()
        form.instance.calculate_solar_panel_capacity_needed()
        form.instance.calculate_no_of_panel()
        form.instance.calculate_total_current()

admin.site.register(Calculation, CalculationAdmin)
admin.site.register(Appliance)
