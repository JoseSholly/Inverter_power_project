from rest_framework import generics, status
from rest_framework.response import Response
from .models import Calculation
from .serializers import CalculationSerializer
from math import ceil

class CalculationCreateView(generics.CreateAPIView):
    serializer_class = CalculationSerializer

    def create(self, request, *args, **kwargs):
        appliances_data = request.data.get('appliances', [])
        backup_time= request.data.get("backup_time",0)
        battery_capacity= request.data.get("battery_capacity",0)
        
        

        total_load = sum(appliance['power_rating'] * appliance['quantity'] for appliance in appliances_data)

         # Calculate Inverter Rating(VA)
        power_factor = 0.8
        inverter_rating = total_load / power_factor

        calculation_data = {
            'total_load': total_load,
            'inverter_rating': inverter_rating,
            'backup_time': backup_time,
            'battery_capacity': battery_capacity
        }

        serializer = self.get_serializer(data=calculation_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Add total_load to the response data
        # Calculate total power needed
        # total_load= sum(appliance["power_rating"] for appliance in appliances_data )
        response_data = serializer.data
        # response_data['total_load'] = total_load

        # calculate battery capacity
        battery_voltage= 12
        inverter_eff= 0.8
        total_battery_capacity=round((total_load * backup_time) / (battery_voltage * inverter_eff))
        response_data['total_battery_capacity'] = total_battery_capacity

        # Number of battery required
        numbers_of_batteries= ceil(total_battery_capacity / battery_capacity)
        # numbers_of_batteries= ceil(total_battery_capacity / 220)
    
        response_data['numbers_of_batteries'] = numbers_of_batteries
    

        return Response(response_data)

class CalculationListView(generics.ListAPIView):
    queryset = Calculation.objects.all()
    serializer_class = CalculationSerializer
