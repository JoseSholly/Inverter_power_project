from rest_framework import serializers
from .models import Calculation

class CalculationSerializer(serializers.ModelSerializer):
    total_load = serializers.FloatField(read_only=True)
    class Meta:
        model = Calculation
        fields = ['id', 'created', 'total_load', 'total_power_needed', 'inverter_power']
    