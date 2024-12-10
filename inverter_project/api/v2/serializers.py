from rest_framework import serializers
from inverter_rating_v2.models import Appliance


class ApplianceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appliance
        fields = ['id', 'name']