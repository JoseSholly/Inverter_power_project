from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
import json
from django.forms.models import model_to_dict
from rest_framework.response import Response
from rest_framework.decorators import api_view

from rest_framework import generics
from .serializers import ApplianceSerializer
from rest_framework.response import Response
from power_calculator.permissions import IsStaffUser
from inverter_rating_v2.models import Appliance

class AppliancesListView(generics.ListAPIView):
    queryset= Appliance.objects.all()
    serializer_class= ApplianceSerializer
