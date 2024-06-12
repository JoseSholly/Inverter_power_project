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
        response_data['battery_voltage']= battery_voltage

        inverter_eff= 0.8
        total_battery_capacity=round((total_load * backup_time) / (battery_voltage * inverter_eff))
        response_data['total_battery_capacity'] = total_battery_capacity

        # Number of battery required
        numbers_of_batteries= ceil(total_battery_capacity / battery_capacity) 
        response_data['numbers_of_batteries'] = numbers_of_batteries


        # Calculate solar panel capacity
        total_energy_req_KWH= (total_load * backup_time) / 1000
        aveage_peak_sun_hour= 5
        total_solar_panel_capacity= round((total_energy_req_KWH / aveage_peak_sun_hour)  * 1000)
        response_data["total_solar_panel_capacity"]= total_solar_panel_capacity


        # calculate number of solar panel
        eff_factor= 0.8
        total_solar_panel_capacity= total_solar_panel_capacity / 0.8

        solar_panel_wattage= 150
        numbers_of_solar_panel= ceil(total_solar_panel_capacity / solar_panel_wattage)

        response_data["numbers_of_solar_panel"]= numbers_of_solar_panel

        # Select Charger controlller
        total_solar_panel_wattage= numbers_of_solar_panel * solar_panel_wattage
        total_current= (total_solar_panel_wattage / battery_voltage) * 1.25 # Add buffer
        response_data["total_current"]= total_current

        return Response(response_data)

class CalculationListView(generics.ListAPIView):
    queryset = Calculation.objects.all()
    serializer_class = CalculationSerializer
