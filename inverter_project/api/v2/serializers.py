from rest_framework import serializers
from inverter_rating_v2.models import Appliance, Calculation, CalculationItem


class ApplianceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appliance
        fields = ['id', 'name']
        ref_name = 'v2_appliance'


class CalculationItemSerializer(serializers.ModelSerializer):
    appliance = ApplianceSerializer()

    class Meta:
        model= CalculationItem
        fields = fields = ['id', 'appliance', 'quantity', 'power_rating', 'backup_time']
        ref_name = 'v2_CalculationItem'

class CalculationSerializer(serializers.ModelSerializer):
    appliance_calc = CalculationItemSerializer(many= True)
    total_load = serializers.FloatField(read_only=True)
    inverter_rating = serializers.FloatField(read_only=True)
    total_battery_capacity = serializers.FloatField(read_only=True)
    numbers_of_batteries = serializers.FloatField(read_only=True)
    total_solar_panel_capacity_needed = serializers.FloatField(read_only=True)
    numbers_of_solar_panel = serializers.FloatField(read_only=True)
    controller_current = serializers.FloatField(read_only=True)

    class Meta:
        model = Calculation
        fields = [
            'id',
            'system_voltage',
            'battery_capacity',
            'solar_panel_watt',
            'total_load',
            'inverter_rating',
            'total_battery_capacity',
            'numbers_of_batteries',
            'total_solar_panel_capacity_needed',
            'numbers_of_solar_panel',
            'controller_current',
            'appliance_calc'

        ]
        ref_name = 'v2_calculation_create'

    def create(self, validated_data):
        calc_items_data = validated_data.pop('appliance_calc')
        calculation = Calculation.objects.create(**validated_data)
        for item_data in calc_items_data:
            appliance_data = item_data.pop('appliance')
            appliance, created = Appliance.objects.get_or_create(**appliance_data)
            CalculationItem.objects.create(calculation=calculation, appliance=appliance, **item_data)
        
        self._calculate(calculation)
        return calculation
    
    def _calculate(self, calcultaion):
        calcultaion.perform_calculation()