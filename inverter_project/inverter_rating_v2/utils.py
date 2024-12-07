from math import ceil

class ApplianceCalculationUtility:
    def  __init__(self, battery_capacity:int, system_voltage:int, solar_panel_watt:int,  items ):

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
        """ 
        Inverter ratings are often expressed in kVA (kilovolt-amperes), which represents the apparent power capacity of the inverter. To convert the power requirements from watts (W) to kVA, you need to account for the power factor (PF), which typically ranges from 0.6 to 0.8 for home appliances.

        Returns:
            Integer: It returns the total inverter rating
        """
        pf = 0.8  # Power factor
        total_inverter_rating = (self.total_load / pf) / 1000
        return total_inverter_rating
    
    
    @property
    def total_battery_cap_required(self):
        """
        Return the total battery capacity required for the system
        """
        inverter_eff = 0.8
        total_energy_consumption = sum(item.power_rating * item.quantity * item.backup_time for item in self.items)

        total_battery_cap = round(total_energy_consumption / (self.system_voltage), 2)

        return total_battery_cap
    
    @property
    def number_of_batteries(self):
        """
        Returns the numbers  of batteries required depending on battery capacity selected 
        """
        total_battery_cap = self.total_battery_cap_required
        number_batteries = total_battery_cap / self.battery_capacity
        number_batteries = ceil(number_batteries)

        return number_batteries
    

    def perform_all_calculations(self):
        self.total_load
        self.total_inverter_rating
        self.total_battery_cap_required
        self.number_of_batteries

    
