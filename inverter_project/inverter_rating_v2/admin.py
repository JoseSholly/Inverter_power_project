# from django.contrib import admin
# from .models import Calculation, CalculationItem, Appliance

# # Register your models here.

# class CalculationItemInline(admin.TabularInline):
#     model= CalculationItem
#     raw_id_fields = ['appliance']
#     fields = ['appliance', 'quantity', 'power_rating', 'backup_time']
#     extra= 1


# class CalculationAdmin(admin.ModelAdmin):
#     list_display = ['id',
#                      'total_load',
#                     'inverter_rating',
#                     'battery_capacity',
#                     'total_battery_capacity',
#                     'numbers_of_batteries',
#                     'total_solar_panel_capacity_needed',
#                     'numbers_of_solar_panel',
#                     'controller_current',
#                     'created',
#                     ]
#     readonly_fields= [
#         'total_load',
#         'inverter_rating',
#         'total_battery_capacity',
#         'numbers_of_batteries',
#         'total_solar_panel_capacity_needed',
#         'numbers_of_solar_panel',
#         'controller_current',
#     ]
#     search_fields = ['id']
#     inlines = [CalculationItemInline]

#     def save_related(self, request, form, formsets, change):
#         super().save_related(request, form, formsets, change)
        
#         # Perform all calculations in a batch and save once
#         form.instance.perform_calculation()


# admin.site.register(Calculation, CalculationAdmin)