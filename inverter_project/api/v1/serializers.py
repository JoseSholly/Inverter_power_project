from rest_framework import serializers
from power_calculator.validators import validate_backup_time, validate_battery_capacity, validate_power_rating
from power_calculator.utils import SystemCalculationUtility
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
    name = serializers.CharField(max_length=100, required=True)
    quantity = serializers.IntegerField(min_value=1, default=1) # Here, quantity is not required by client, default is used if missing
    power_rating = serializers.IntegerField(validators=[validate_power_rating], default=1) # Same for power_rating

class SolarSystemCalculationSerializer(serializers.Serializer):
    # Input fields - client MUST provide these values
    backup_time = serializers.IntegerField(
        required=True, # Client must provide this
        help_text="How many hours of backup you need during a power outage.",
        validators=[validate_backup_time]
    )
    battery_capacity = serializers.ChoiceField(
        choices=BATTERY_CAPACITY_CHOICES,
        required=True, # Client must provide this
        validators=[validate_battery_capacity]
    )
    system_voltage = serializers.ChoiceField(
        choices=BATTERY_VOLTAGE_CHOICES,
        required=True # Client must provide this
    )
    solar_panel_watt = serializers.ChoiceField(
        choices=SOLAR_PANEL_WATT,
        required=True # Client must provide this
    )
    items = ApplianceInputSerializer(many=True, required=True) # Client must provide a list of items

    # Output fields (read-only, populated after calculations)
    total_load = serializers.FloatField(read_only=True)
    inverter_rating = serializers.FloatField(read_only=True)
    total_battery_capacity = serializers.FloatField(read_only=True)
    numbers_of_batteries = serializers.IntegerField(read_only=True)
    total_solar_panel_capacity_needed = serializers.FloatField(read_only=True)
    numbers_of_solar_panel = serializers.IntegerField(read_only=True)
    total_current = serializers.FloatField(read_only=True)

    def _perform_calculation_logic(self, data):
        """
        Helper method to encapsulate the calculation logic, used by both create and update.
        """
        calc_utility = SystemCalculationUtility(
            total_load=0, # Initial value, will be calculated by the utility
            backup_time=data['backup_time'],
            battery_capacity=data['battery_capacity'],
            system_voltage=data['system_voltage'],
            solar_panel_watt=data['solar_panel_watt'],
            items=data['items']
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
            # Echo input values as well
            'backup_time': data['backup_time'],
            'battery_capacity': data['battery_capacity'],
            'system_voltage': data['system_voltage'],
            'solar_panel_watt': data['solar_panel_watt'],
            'items': data['items'],
        }

    def create(self, validated_data):
        """
        Handles initial calculation (analogous to POST).
        """
        return self._perform_calculation_logic(validated_data)

    def update(self, instance, validated_data):
        """
        Handles re-calculation based on updated input (analogous to PUT/PATCH).
        'instance' here is the previous output dictionary, not a model instance.
        'validated_data' contains the new, potentially partial, input.
        """
        # Create a mutable copy of the instance data
        updated_data = instance.copy()

        # Update the instance data with the validated (new) data
        for field, value in validated_data.items():
            if field == 'items':
                # For 'items', you might need more sophisticated merging logic
                # For simplicity here, we'll replace the entire list if provided
                updated_data['items'] = value
            else:
                updated_data[field] = value
        
        # Now, re-run the calculations with the combined data
        return self._perform_calculation_logic(updated_data)
