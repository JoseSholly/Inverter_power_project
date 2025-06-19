from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import SolarSystemCalculationSerializer, ApplianceSerializer
from drf_yasg.utils import swagger_auto_schema
from power_calculator.models import Appliance


class SolarCalculationAPIView(APIView):
    http_method_names = ["post"]

    @swagger_auto_schema(request_body=SolarSystemCalculationSerializer, tags=["Power Calculation"])
    def post(self, request, *args, **kwargs):
        """
        Performs a new solar system calculation based on the provided input data.
        Every POST request is treated as a new, independent calculation.
        """
        serializer = SolarSystemCalculationSerializer(data=request.data)

        # Validate the incoming data
        if serializer.is_valid(raise_exception=True):
            # If data is valid, perform the calculations.
            # The .save() method on a serializer (without a model instance)
            # will call the .create() method defined in your serializer,
            # which we've designed to run all the calculation logic.
            calculated_results = serializer.save()

            # Return the calculated results with a 201 Created status
            return Response(calculated_results, status=status.HTTP_201_CREATED)


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
