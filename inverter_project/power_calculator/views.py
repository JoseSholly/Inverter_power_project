from django.shortcuts import render
from rest_framework import generics, mixins, serializers
from .models import Appliance
from .serializers import ApplianceSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import Http404


class ApplianceListCreateAPIView(generics.ListCreateAPIView):
    queryset= Appliance.objects.all()
    serializer_class= ApplianceSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data)
    
class InverterPowerView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        appliances = Appliance.objects.all()
        total_power_needed = sum(appliance.total_power for appliance in appliances)
        inverter_power = total_power_needed * 1.25  # Adding 25% buffer
        return Response({'total_power_needed': total_power_needed, 'inverter_power': inverter_power})