from rest_framework import serializers
from .models import Calculation

class CalculationSerializer(serializers.ModelSerializer):
    total_battery_capacity = serializers.FloatField(read_only=True)
    # inverter_rating = serializers.FloatField(read_only=True)
    numbers_of_batteries= serializers.FloatField(read_only=True)
    total_solar_panel_capacity= serializers.FloatField(read_only= True)
    class Meta:
        model = Calculation
        fields = ['id', 'created',"backup_time", 'total_load', 'inverter_rating',"total_battery_capacity", "numbers_of_batteries", "battery_capacity", "total_solar_panel_capacity", ]
    