from rest_framework import serializers
from power_calculator.validators import validate_backup_time, validate_battery_capacity, validate_power_rating
from power_calculator.utils import SystemCalculationUtility
from power_calculator.models import Appliance
BATTERY_VOLTAGE_CHOICES = [
    (12, '12V'),
    (24, '24V'),
    (48, '48V'),
]

BATTERY_CAPACITY_CHOICES = [
    (150, '150Ah 12V'),
    (200, '200Ah 12V'),
    (220, '220Ah 12V'),
    (250, '250Ah 12V'),
]

SOLAR_PANEL_WATT = [
    (300, '300W'),
    (350, '350W'),
    (400, '400W'),
    (450, '450W'),
]

# --- New: Django REST Framework Serializers ---

class ApplianceInputSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True, min_value=1)
    quantity = serializers.IntegerField(min_value=1, default=1) # Here, quantity is not required by client, default is used if missing
    power_rating = serializers.IntegerField(validators=[validate_power_rating], default=1) # Same for power_rating
    

    def validate_id(self, value):
        # Now, validate against the database
        try:
            Appliance.objects.get(id=value)
        except Appliance.DoesNotExist:
            raise serializers.ValidationError(f"Appliance with ID {value} does not exist in the database.")
        return value


    

class SolarSystemCalculationSerializer(serializers.Serializer):
    # Input fields - client MUST provide these values
    backup_time = serializers.IntegerField(
        required=True, 
        help_text="How many hours of backup you need during a power outage.",
        validators=[validate_backup_time]
    )
    battery_capacity = serializers.ChoiceField(
        choices=BATTERY_CAPACITY_CHOICES,
        required=True, 
        validators=[validate_battery_capacity]
    )
    system_voltage = serializers.ChoiceField(
        choices=BATTERY_VOLTAGE_CHOICES,
        required=True 
    )
    solar_panel_watt = serializers.ChoiceField(
        choices=SOLAR_PANEL_WATT,
        required=True 
    )
    # This 'items' field is now for INPUT ONLY
    items = ApplianceInputSerializer(many=True, required=True, write_only=True) 

    # Output fields (read-only, populated after calculations)
    total_load = serializers.FloatField(read_only=True)
    inverter_rating = serializers.FloatField(read_only=True)
    total_battery_capacity = serializers.FloatField(read_only=True)
    numbers_of_batteries = serializers.IntegerField(read_only=True)
    total_solar_panel_capacity_needed = serializers.FloatField(read_only=True)
    numbers_of_solar_panel = serializers.IntegerField(read_only=True)
    total_current = serializers.FloatField(read_only=True)

    # This 'items_details' field is for OUTPUT, and will include appliance names
    items_details = serializers.SerializerMethodField() 

    def get_items_details(self, obj):
        return obj.get('resolved_items_for_output', [])


    def _perform_calculation_logic(self, data):
        """
        Helper method to encapsulate the calculation logic, used by both create and update.
        This method now resolves appliance details from the database.
        """
        processed_items_for_utility = []
        resolved_items_for_output = [] # This list will populate the 'items_details' output field

        # Fetch all required appliance objects from the database in a single query for efficiency
        appliance_ids_in_request = [item_input['id'] for item_input in data['items']]
        appliances_from_db = Appliance.objects.in_bulk(appliance_ids_in_request) 

        for item_input in data['items']:
            appliance_id = item_input['id']
            appliance_obj = appliances_from_db.get(appliance_id)

            if not appliance_obj:
                raise serializers.ValidationError(f"Appliance with ID {appliance_id} not found during calculation.")

            
            # Prepare item for SystemCalculationUtility (needs name, quantity, power_rating)
            processed_items_for_utility.append({
                'name': appliance_obj.name, 
                'quantity': item_input['quantity'],
                'power_rating': item_input['power_rating']
            })
            
            # Prepare item for the API response (items_details field)
            resolved_items_for_output.append({
                'id': appliance_id,
                'name': appliance_obj.name, 
                'quantity': item_input['quantity'],
                'power_rating': item_input['power_rating'], 
            })


        calc_utility = SystemCalculationUtility(
            total_load=0, 
            backup_time=data['backup_time'],
            battery_capacity=data['battery_capacity'],
            system_voltage=data['system_voltage'],
            solar_panel_watt=data['solar_panel_watt'],
            items=processed_items_for_utility 
        )
        calc_utility.perform_all_calculations()

        return {
            'total_load': calc_utility.total_load,
            'inverter_rating': calc_utility.inverter_rating,
            'total_battery_capacity': calc_utility.total_battery_capacity,
            'numbers_of_batteries': calc_utility.numbers_of_batteries,
            'total_solar_panel_capacity_needed': calc_utility.total_solar_panel_capacity_needed,
            'numbers_of_solar_panel': calc_utility.numbers_of_solar_panel,
            'total_current': calc_utility.total_current,
            
            'backup_time': data['backup_time'],
            'battery_capacity': data['battery_capacity'],
            'system_voltage': data['system_voltage'],
            'solar_panel_watt': data['solar_panel_watt'],
            
            'items': resolved_items_for_output 
        }

    def create(self, validated_data):
        return self._perform_calculation_logic(validated_data)

    def update(self, instance, validated_data):
        updated_data = instance.copy()

        for field, value in validated_data.items():
            if field == 'items':
                updated_data['items'] = value
            else:
                updated_data[field] = value
        
        return self._perform_calculation_logic(updated_data)

class ApplianceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appliance
        fields= ["id", "name"]
        read_only= ["id", "name"]