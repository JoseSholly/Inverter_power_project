from math import ceil

# --- SystemCalculationUtility Class (remains the same) ---
class SystemCalculationUtility:
    def __init__(self, total_load, backup_time, battery_capacity, system_voltage, solar_panel_watt, items):
        self.total_load = total_load
        self.backup_time = backup_time
        self.battery_capacity = battery_capacity
        self.system_voltage = system_voltage
        self.solar_panel_watt = solar_panel_watt
        self.items = items

        # Output fields
        self.inverter_rating = 0
        self.total_battery_capacity = 0
        self.numbers_of_batteries = 0
        self.total_solar_panel_capacity_needed = 0
        self.numbers_of_solar_panel = 0
        self.total_current = 0

    def calculate_total_load(self):
        """
        Computes the total load based on the power rating and quantity of each appliance associated with the calculation.
        """
        # Ensure items is treated as a list of dicts, as it comes from serializer
        self.total_load = sum(item['power_rating'] * item['quantity'] for item in self.items)
        return self.total_load

    def calculate_total_inverter_rating(self):
        pf = 0.8  # Power factor
        self.inverter_rating = (self.total_load / pf) / 1000
        return self.inverter_rating

    def calculate_total_battery_capacity(self):
        inverter_eff = 0.8
        self.total_battery_capacity = round((self.total_load * self.backup_time) / (self.system_voltage * inverter_eff), 2)
        return self.total_battery_capacity

    def calculate_no_of_battery(self):
        individual_battery_volt = 12
        if self.system_voltage != 12:
            self.numbers_of_batteries = ceil(self.system_voltage / individual_battery_volt)
        else:
            self.numbers_of_batteries = ceil(self.total_battery_capacity / self.battery_capacity)
        return self.numbers_of_batteries

    def calculate_solar_panel_capacity_needed(self):
        total_energy_req_KWH = (self.total_load * self.backup_time) / 1000
        average_peak_sun_hour = 6
        total_solar_panel_capacity = round((total_energy_req_KWH / average_peak_sun_hour) * 1000)
        inverter_eff = 0.8
        self.total_solar_panel_capacity_needed = total_solar_panel_capacity / inverter_eff
        return self.total_solar_panel_capacity_needed

    def get_no_panel(self, required_capacity, panel_capacity):
        solution = ceil(required_capacity / panel_capacity)
        return solution

    def calculate_no_of_panel(self):
        self.numbers_of_solar_panel = round(ceil(self.get_no_panel(
            required_capacity=self.total_solar_panel_capacity_needed,
            panel_capacity=self.solar_panel_watt
        )))
        return self.numbers_of_solar_panel

    def calculate_total_current(self):
        total_solar_panel_wattage = self.numbers_of_solar_panel * self.solar_panel_watt
        self.total_current = round(total_solar_panel_wattage / self.system_voltage, 2)
        return self.total_current

    def perform_all_calculations(self):
        self.calculate_total_load()
        self.calculate_total_inverter_rating()
        self.calculate_total_battery_capacity()
        self.calculate_no_of_battery()
        self.calculate_solar_panel_capacity_needed()
        self.calculate_no_of_panel()
        self.calculate_total_current()

