from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from power_calculator.models import Appliance
from .serializers import ApplianceSerializer, CalculationResultSerializer
from drf_yasg.utils import swagger_auto_schema


class ApplianceListView(APIView):
    """
    API View to list all available appliances from the database.
    """
    def get(self, request, *args, **kwargs):
        # Fetch all Appliance objects from the database
        appliances = Appliance.objects.all()
        # Serialize the queryset using the ModelSerializer
        serializer = ApplianceSerializer(appliances, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
class PerformCalculationView(APIView):
    """
    API endpoint to receive calculation inputs and return computed results while considering individual backup
    It does not store calculation instances in the database.
    """
    http_method_names = ['post']

    @swagger_auto_schema(request_body=CalculationResultSerializer, tags=["v2"])
    def post(self, request, *args, **kwargs):
        # Instantiate your CalculationResultSerializer with the request data
        serializer = CalculationResultSerializer(data=request.data)
        
        # Validate the incoming data. If invalid, it will raise an exception
        # and return a 400 Bad Request response automatically.
        serializer.is_valid(raise_exception=True) 
        
        # Call .save() on the serializer. For non-model serializers, this
        # triggers the create() method, which in our case returns the
        # dictionary of input data combined with calculated results.
        calculated_data = serializer.save() 
        
        # Return the calculated data as a successful HTTP 200 OK response.
        return Response(calculated_data, status=status.HTTP_200_OK)