from rest_framework import serializers
from .models import Appliance

class ApplianceSerializer(serializers.ModelSerializer):
    total_power = serializers.ReadOnlyField()

    class Meta:
        model = Appliance
        fields = ['name', 'power_rating', 'quantity', 'total_power']
