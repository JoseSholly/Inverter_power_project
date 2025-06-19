from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import SolarSystemCalculationSerializer # Assuming your serializer is in serializers.py

class SolarCalculationAPIView(APIView):

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

        # If serializer.is_valid() returns False, raise_exception=True will
        # automatically return a 400 Bad Request with validation errors,
        # so an explicit else block here is not strictly necessary but can be added
        # for custom error handling if needed.
        # else:
        #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)