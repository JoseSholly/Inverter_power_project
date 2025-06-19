from rest_framework import serializers
from inverter_rating_v2.utils import ApplianceCalculationUtility
from inverter_rating_v2.models import Appliance 


class ApplianceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appliance
        fields = ['id', 'name']
        ref_name = 'v2_appliance'

class ApplianceCalculationInputSerializer(serializers.Serializer):
    """
    Defines the expected structure for each appliance item in the calculation request.
    It now accepts an 'id' (integer) and manually validates it against the Appliance model.
    """
    id = serializers.IntegerField(required=True, min_value=1) # Appliance ID
    quantity = serializers.IntegerField(min_value=1, required=True)
    power_rating = serializers.FloatField(min_value=0.01, required=True) # Power in Watts (W)
    backup_time = serializers.FloatField(min_value=0.01, required=True) # Backup time in hours

    # We will manually add 'name' to the representation in to_representation
    # We no longer need _appliance_instance here, as the parent serializer
    # will prepare the data for us.

    def validate(self, data):
        """
        Custom validation to lookup the Appliance by ID and store its instance
        within the 'data' dictionary for the parent serializer's use.
        """
        appliance_id = data.get('id')
        try:
            # Attempt to fetch the Appliance instance
            # This instance will be used by the parent serializer to get the name
            # and by the utility if needed (though utility only needs power_rating, etc.)
            data['appliance_instance'] = Appliance.objects.get(id=appliance_id) 
        except Appliance.DoesNotExist:
            raise serializers.ValidationError(
                {'id': f"Appliance with ID {appliance_id} does not exist."}
            )
        return data

    def to_representation(self, instance):
        """
        Override to include the appliance name in the output.
        'instance' here will be the dictionary *already prepared* by the parent
        serializer (CalculationResultSerializer) which will contain 'id' and 'name'.
        """
        # Get the default representation (id, quantity, power_rating, backup_time)
        representation = super().to_representation(instance)
        
        # Add the appliance name from the instance dictionary itself
        # The parent serializer's _calculate_all method will ensure 'name' is here.
        if 'name' in instance: # Check if 'name' is already provided in the instance data
            representation['name'] = instance['name']
        # If for some reason 'name' isn't there, you might want a fallback
        # (e.g., fetching from DB, but this should ideally be avoided in to_representation
        # as it can lead to N+1 queries if not careful).
        elif 'id' in instance:
            try:
                # This fallback is less efficient but ensures name is present if upstream
                # logic doesn't explicitly add it. Optimize if performance is critical.
                appliance_instance = Appliance.objects.get(id=instance['id'])
                representation['name'] = appliance_instance.name
            except Appliance.DoesNotExist:
                representation['name'] = None # Or handle error appropriately
                
        return representation


class CalculationResultSerializer(serializers.Serializer):
    """
    A non-model serializer that takes system parameters and appliance details
    as input, performs calculations using ApplianceCalculationUtility, and returns the results.
    """
    system_voltage = serializers.FloatField(min_value=1.0, required=True) # Volts (V)
    battery_capacity = serializers.FloatField(min_value=1.0, required=True) # Battery capacity in Ampere-hours (Ah)
    solar_panel_watt = serializers.FloatField(min_value=1.0, required=True) # Solar panel rating in Watts-peak (Wp)

    items = ApplianceCalculationInputSerializer(many=True, required=True)

    total_load = serializers.SerializerMethodField()
    inverter_rating = serializers.SerializerMethodField()
    total_battery_capacity = serializers.SerializerMethodField()
    numbers_of_batteries = serializers.SerializerMethodField()
    total_solar_panel_capacity_needed = serializers.SerializerMethodField()
    numbers_of_solar_panel = serializers.SerializerMethodField()
    controller_current = serializers.SerializerMethodField()

    _calculated_data = {}

    def validate(self, data):
        self._calculate_all(data)
        return data

    def create(self, validated_data):
        # 'create' for a non-model serializer simply returns the processed data.
        return self._calculated_data

    def _calculate_all(self, data):
        """
        Internal method to encapsulate all calculation logic,
        delegating to ApplianceCalculationUtility.
        Crucially, this method prepares the 'items' data to be JSON serializable
        for storage in _calculated_data.
        """
        processed_items_for_utility = []
        final_output_items = [] # This list will hold dicts ready for JSON serialization

        for item_data in data.get('items', []):
            # The ApplianceCalculationInputSerializer's validate method added 'appliance_instance'
            appliance_instance = item_data['appliance_instance']

            # Prepare data for the utility (only needs power_rating, quantity, backup_time)
            processed_items_for_utility.append({
                'power_rating': item_data['power_rating'],
                'quantity': item_data['quantity'],
                'backup_time': item_data['backup_time'],
            })

            # Prepare data for the *final output*, including 'id' and 'name'
            final_output_items.append({
                'id': appliance_instance.id, # Use id
                'name': appliance_instance.name, # Use name
                'quantity': item_data['quantity'],
                'power_rating': item_data['power_rating'],
                'backup_time': item_data['backup_time'],
            })

        battery_capacity = data.get('battery_capacity')
        system_voltage = data.get('system_voltage')
        solar_panel_watt = data.get('solar_panel_watt')

        calculator = ApplianceCalculationUtility(
            battery_capacity=battery_capacity,
            system_voltage=system_voltage,
            solar_panel_watt=solar_panel_watt,
            items=processed_items_for_utility # Utility only needs these values
        )

        calculated_results = {
            'total_load': calculator.total_load,
            'inverter_rating': calculator.inverter_rating,
            'total_battery_capacity': calculator.total_battery_cap_required,
            'numbers_of_batteries': calculator.number_of_batteries,
            'total_solar_panel_capacity_needed': calculator.total_solar_capacity,
            'numbers_of_solar_panel': calculator.number_of_panels,
            'controller_current': calculator.controller_current,
        }

        # Store the combined input data and calculated results.
        # Ensure the 'items' here are the JSON-serializable dictionaries.
        self._calculated_data = {
            
            'system_voltage': data.get('system_voltage'),
            'battery_capacity': data.get('battery_capacity'),
            'solar_panel_watt': data.get('solar_panel_watt'),
            **calculated_results,
            'items': final_output_items, # Store the list of dictionaries with id and name
            
        }

    # SerializerMethodField implementations (no change needed here as they fetch from _calculated_data)
    def get_total_load(self, obj):
        return self._calculated_data.get('total_load')

    def get_inverter_rating(self, obj):
        return self._calculated_data.get('inverter_rating')

    def get_total_battery_capacity(self, obj):
        return self._calculated_data.get('total_battery_capacity')

    def get_numbers_of_batteries(self, obj):
        return self._calculated_data.get('numbers_of_batteries')

    def get_total_solar_panel_capacity_needed(self, obj):
        return self._calculated_data.get('total_solar_panel_capacity_needed')

    def get_numbers_of_solar_panel(self, obj):
        return self._calculated_data.get('numbers_of_solar_panel')

    def get_controller_current(self, obj):
        return self._calculated_data.get('controller_current')