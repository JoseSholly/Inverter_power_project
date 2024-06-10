from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
import json
from power_calculator.models import Appliance
from django.forms.models import model_to_dict
from rest_framework.response import Response
from rest_framework.decorators import api_view
from power_calculator.serializers import ApplianceSerializer
# Create your views here.

@api_view(["POST"])
def api_home(request, *args, **kawrgs):
    """
    DRF API VIEW
    """

    serializer= ApplianceSerializer(data= request.data)
    if serializer.is_valid(raise_exception=True):
        # instance= serializer.save()
        print(serializer.data)
    
        return Response(serializer.data)
    return Response({"Invalid": "Bad data input"}, status=400)