from math import ceil

class ApplianceCalculationUtility:
    def  __init__(self, battery_capacity, system_voltage, solar_panel_watt,  items ):

        self.battery_capacity = battery_capacity
        self.system_voltage = system_voltage
        self.solar_panel_watt = solar_panel_watt
        self.items= items


    
    @property
    def total_load(self):
        """
        Computes the total load based on the power rating and quantity of each appliance associated with the calculation.
        """
        total_load = sum(item.power_rating * item.quantity for item in self.items)
        return total_load
    @property
    def total_inverter_rating(self):
        pf = 0.8  # Power factor
        total_inverter_rating = (self.total_load / pf) / 1000
        return total_inverter_rating


    def perform_all_calculations(self):
        self.total_load
        self.total_inverter_rating
    
