from rest_framework import generics, status
from rest_framework.response import Response
from .models import Calculation
from .serializers import CalculationSerializer

class CalculationCreateView(generics.CreateAPIView):
    serializer_class = CalculationSerializer

    def create(self, request, *args, **kwargs):
        appliances_data = request.data.get('appliances', [])
        
        

        total_power_needed = sum(appliance['power_rating'] * appliance['quantity'] for appliance in appliances_data)

        inverter_power = total_power_needed * 1.25  # Adding 25% buffer

        calculation_data = {
            'total_power_needed': total_power_needed,
            'inverter_power': inverter_power,
        }

        serializer = self.get_serializer(data=calculation_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Add total_load to the response data
        # Calculate total power needed
        total_load= sum(appliance["power_rating"] for appliance in appliances_data )
        response_data = serializer.data
        response_data['total_load'] = total_load

        

        return Response(response_data)

class CalculationListView(generics.ListAPIView):
    queryset = Calculation.objects.all()
    serializer_class = CalculationSerializer
