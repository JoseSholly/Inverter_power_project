from rest_framework import serializers
from .models import Calculation

class CalculationSerializer(serializers.ModelSerializer):
    battery_capacity = serializers.FloatField(read_only=True)
    # inverter_rating = serializers.FloatField(read_only=True)
    class Meta:
        model = Calculation
        fields = ['id', 'created',"backup_time", 'total_load', 'inverter_rating',"battery_capacity" ]
    