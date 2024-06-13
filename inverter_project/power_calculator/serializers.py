from rest_framework import serializers
from .models import Appliance, Calculation, CalculationItem

class ApplianceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appliance
        fields = ['id', 'name', 'created']

class CalculationItemSerializer(serializers.ModelSerializer):
    appliance = ApplianceSerializer()

    class Meta:
        model = CalculationItem
        fields = ['id', 'appliance', 'quantity', 'power_rating']

class CalculationSerializer(serializers.ModelSerializer):
    calc = CalculationItemSerializer(many=True)
    total_load = serializers.FloatField(read_only=True)
    inverter_rating = serializers.FloatField(read_only=True)
    total_battery_capacity = serializers.FloatField(read_only=True)
    numbers_of_batteries = serializers.FloatField(read_only=True)
    total_solar_panel_capacity_needed = serializers.FloatField(read_only=True)
    numbers_of_solar_panel = serializers.FloatField(read_only=True)
    total_current = serializers.FloatField(read_only=True)

    class Meta:
        model = Calculation
        fields = [
            'id', 'total_load', 'inverter_rating', 'backup_time', 'battery_capacity', 
            'system_voltage', 'total_battery_capacity', 'numbers_of_batteries', 
            'total_solar_panel_capacity_needed', 'solar_panel_watt', 'numbers_of_solar_panel', 
            'total_current', 'created', 'updated', 'calc'
        ]

    def create(self, validated_data):
        calc_items_data = validated_data.pop('calc')
        calculation = Calculation.objects.create(**validated_data)
        for item_data in calc_items_data:
            appliance_data = item_data.pop('appliance')
            appliance, created = Appliance.objects.get_or_create(**appliance_data)
            CalculationItem.objects.create(calculation=calculation, appliance=appliance, **item_data)
        
        calculation.calculate_total_load()
        calculation.calculate_total_inverter_rating()
        calculation.calculate_total_battery_capacity()
        calculation.calculate_no_of_battery()
        calculation.calculate_solar_panel_capacity_needed()
        calculation.calculate_no_of_panel()
        calculation.calculate_total_current()
        
        return calculation
