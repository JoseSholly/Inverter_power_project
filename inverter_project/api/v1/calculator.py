"""v1 sizing math: one backup time shared by every appliance.

Pure Python: no Django or HTTP imports, so it can be unit-tested in isolation.
"""
from dataclasses import dataclass
from math import ceil

POWER_FACTOR = 0.8
INVERTER_EFFICIENCY = 0.8
AVERAGE_PEAK_SUN_HOURS = 6
BATTERY_UNIT_VOLTAGE = 12


@dataclass(frozen=True)
class LoadItem:
    quantity: int
    power_rating: int


@dataclass(frozen=True)
class V1CalculationInput:
    backup_time: int
    battery_capacity: int
    system_voltage: int
    solar_panel_watt: int
    items: tuple[LoadItem, ...]


@dataclass(frozen=True)
class V1CalculationOutput:
    total_load: int
    inverter_rating: float
    total_battery_capacity: float
    numbers_of_batteries: int
    total_solar_panel_capacity_needed: float
    numbers_of_solar_panel: int
    total_current: float


class V1Calculator:
    def calculate(self, data: V1CalculationInput) -> V1CalculationOutput:
        total_load = self.total_load(data.items)
        total_battery_capacity = self.total_battery_capacity(total_load, data.backup_time, data.system_voltage)
        solar_capacity = self.solar_panel_capacity_needed(total_load, data.backup_time)
        panels = self.number_of_panels(solar_capacity, data.solar_panel_watt)
        return V1CalculationOutput(
            total_load=total_load,
            inverter_rating=self.inverter_rating(total_load),
            total_battery_capacity=total_battery_capacity,
            numbers_of_batteries=self.number_of_batteries(
                total_battery_capacity, data.battery_capacity, data.system_voltage
            ),
            total_solar_panel_capacity_needed=solar_capacity,
            numbers_of_solar_panel=panels,
            total_current=self.total_current(panels, data.solar_panel_watt, data.system_voltage),
        )

    @staticmethod
    def total_load(items: tuple[LoadItem, ...]) -> int:
        return sum(item.power_rating * item.quantity for item in items)

    @staticmethod
    def inverter_rating(total_load: float) -> float:
        """Inverter size in kVA."""
        return round((total_load / POWER_FACTOR) / 1000, 2)

    @staticmethod
    def total_battery_capacity(total_load: float, backup_time: float, system_voltage: int) -> float:
        """Battery bank capacity in Ah at the system voltage."""
        return round((total_load * backup_time) / (system_voltage * INVERTER_EFFICIENCY), 2)

    @staticmethod
    def number_of_batteries(total_battery_capacity: float, battery_capacity: int, system_voltage: int) -> int:
        """12V batteries needed: batteries in series per string x parallel strings."""
        batteries_per_string = ceil(system_voltage / BATTERY_UNIT_VOLTAGE)
        strings = ceil(total_battery_capacity / battery_capacity)
        return batteries_per_string * strings

    @staticmethod
    def solar_panel_capacity_needed(total_load: float, backup_time: float) -> float:
        """Solar array size in W."""
        energy_kwh = (total_load * backup_time) / 1000
        capacity = round((energy_kwh / AVERAGE_PEAK_SUN_HOURS) * 1000)
        return capacity / INVERTER_EFFICIENCY

    @staticmethod
    def number_of_panels(required_capacity: float, panel_watt: int) -> int:
        return ceil(required_capacity / panel_watt)

    @staticmethod
    def total_current(number_of_panels: int, panel_watt: int, system_voltage: int) -> float:
        return round((number_of_panels * panel_watt) / system_voltage, 2)
