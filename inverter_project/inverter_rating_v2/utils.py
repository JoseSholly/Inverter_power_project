from math import ceil

class ApplianceCalculationUtility:
    def __init__(self, battery_capacity: float, system_voltage: float, solar_panel_watt: float, items: list[dict]):
        self.battery_capacity = battery_capacity
        self.system_voltage = system_voltage
        self.solar_panel_watt = solar_panel_watt
        self.items = items # This will now be a list of dictionaries

    @property
    def total_load(self) -> float:
        """
        Computes the total load based on the power rating and quantity of each appliance.
        """
        # Access dictionary keys instead of attributes
        total_load = sum(item['power_rating'] * item['quantity'] for item in self.items)
        return round(total_load, 2)

    @property
    def inverter_rating(self) -> float:
        """
        Inverter ratings are often expressed in kVA. Converts total load from Watts to kVA.
        """
        pf = 0.8  # Power factor
        total_inverter_rating_kVA = (self.total_load / pf) / 1000
        return round(total_inverter_rating_kVA, 2)

    @property
    def total_battery_cap_required(self) -> float:
        """
        Return the total battery capacity required for the system in Ah.
        """
        # Calculate total energy consumption in Watt-hours (Wh)
        total_energy_consumption_wh = sum(item['power_rating'] * item['quantity'] * item['backup_time'] for item in self.items)
        
        # Convert Wh to Ah: Ah = Wh / V_system
        if self.system_voltage > 0:
            total_battery_cap_ah = total_energy_consumption_wh / self.system_voltage
        else:
            total_battery_cap_ah = 0
        return round(total_battery_cap_ah, 2)

    @property
    def number_of_batteries(self) -> int:
        """
        Returns the number of batteries required based on total capacity and selected battery capacity.
        """
        total_battery_cap_ah = self.total_battery_cap_required
        if self.battery_capacity > 0:
            number_batteries = ceil(total_battery_cap_ah / self.battery_capacity)
        else:
            number_batteries = 0
        return int(number_batteries)

    @property
    def total_solar_capacity(self) -> float:
        """
        Calculates the total solar panel capacity needed in Watts-peak (Wp).
        """
        total_energy_consumption_wh = sum(item['power_rating'] * item['quantity'] * item['backup_time'] for item in self.items)
        
        # Adjust for system losses (e.g., 80% efficiency)
        system_loss_factor = 0.8
        adjusted_energy_wh = total_energy_consumption_wh / system_loss_factor
        
        peak_sun_hours = 6  # Typical average peak sun hours per day
        if peak_sun_hours > 0:
            total_solar_cap_wp = adjusted_energy_wh / peak_sun_hours
        else:
            total_solar_cap_wp = 0
        return round(total_solar_cap_wp, 2)

    @property
    def number_of_panels(self) -> int:
        """
        Returns the number of solar panels required based on total solar capacity and individual panel wattage.
        """
        total_solar_cap_wp = self.total_solar_capacity
        if self.solar_panel_watt > 0:
            no_of_panels = ceil(total_solar_cap_wp / self.solar_panel_watt)
        else:
            no_of_panels = 0
        return int(no_of_panels)

    @property
    def controller_current(self) -> float:
        """
        Calculates the required charge controller current in Amps.
        """
        total_solar_cap_wp = self.total_solar_capacity
        # Apply a 25% safety factor (1.25)
        if self.system_voltage > 0:
            current_amps = (total_solar_cap_wp * 1.25) / self.system_voltage
        else:
            current_amps = 0
        return round(current_amps, 2)


    # def perform_all_calculations(self):
    #     # Calling properties will execute their logic
    #     _ = self.total_load
    #     _ = self.inverter_rating
    #     _ = self.total_battery_cap_required
    #     _ = self.number_of_batteries
    #     _ = self.total_solar_capacity
    #     _ = self.controller_current


    
