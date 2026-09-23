"""v2 sizing math: every appliance has its own backup time.

Pure Python: no Django or HTTP imports, so it can be unit-tested in isolation.
"""
from dataclasses import dataclass
from math import ceil

POWER_FACTOR = 0.8
SYSTEM_LOSS_FACTOR = 0.8
PEAK_SUN_HOURS = 6
CONTROLLER_SAFETY_FACTOR = 1.25
BATTERY_UNIT_VOLTAGE = 12


@dataclass(frozen=True)
class LoadItem:
    quantity: int
    power_rating: float
    backup_time: float

    @property
    def power(self) -> float:
        """Power draw in W."""
        return self.power_rating * self.quantity

    @property
    def energy(self) -> float:
        """Energy needed in Wh."""
        return self.power * self.backup_time


@dataclass(frozen=True)
class V2CalculationInput:
    battery_capacity: float
    system_voltage: float
    solar_panel_watt: float
    items: tuple[LoadItem, ...]


@dataclass(frozen=True)
class V2CalculationOutput:
    total_load: float
    inverter_rating: float
    total_battery_capacity: float
    numbers_of_batteries: int
    total_solar_panel_capacity_needed: float
    numbers_of_solar_panel: int
    controller_current: float


class V2Calculator:
    def calculate(self, data: V2CalculationInput) -> V2CalculationOutput:
        total_load = self.total_load(data.items)
        total_energy = self.total_energy(data.items)
        battery_capacity_needed = self.total_battery_capacity(total_energy, data.system_voltage)
        solar_capacity = self.solar_capacity(total_energy)
        return V2CalculationOutput(
            total_load=total_load,
            inverter_rating=self.inverter_rating(total_load),
            total_battery_capacity=battery_capacity_needed,
            numbers_of_batteries=self.number_of_batteries(
                battery_capacity_needed, data.battery_capacity, data.system_voltage
            ),
            total_solar_panel_capacity_needed=solar_capacity,
            numbers_of_solar_panel=self.number_of_panels(solar_capacity, data.solar_panel_watt),
            controller_current=self.controller_current(solar_capacity, data.system_voltage),
        )

    @staticmethod
    def total_load(items: tuple[LoadItem, ...]) -> float:
        return round(sum(item.power for item in items), 2)

    @staticmethod
    def total_energy(items: tuple[LoadItem, ...]) -> float:
        return sum(item.energy for item in items)

    @staticmethod
    def inverter_rating(total_load: float) -> float:
        """Inverter size in kVA."""
        return round((total_load / POWER_FACTOR) / 1000, 2)

    @staticmethod
    def total_battery_capacity(total_energy_wh: float, system_voltage: float) -> float:
        """Battery bank capacity in Ah at the system voltage."""
        if system_voltage <= 0:
            return 0
        return round(total_energy_wh / system_voltage, 2)

    @staticmethod
    def number_of_batteries(total_battery_capacity: float, battery_capacity: float, system_voltage: float) -> int:
        """12V batteries needed: batteries in series per string x parallel strings."""
        if battery_capacity <= 0 or system_voltage <= 0:
            return 0
        batteries_per_string = ceil(system_voltage / BATTERY_UNIT_VOLTAGE)
        strings = ceil(total_battery_capacity / battery_capacity)
        return int(batteries_per_string * strings)

    @staticmethod
    def solar_capacity(total_energy_wh: float) -> float:
        """Solar array size in Wp, adjusted for system losses."""
        adjusted_energy = total_energy_wh / SYSTEM_LOSS_FACTOR
        return round(adjusted_energy / PEAK_SUN_HOURS, 2)

    @staticmethod
    def number_of_panels(solar_capacity: float, panel_watt: float) -> int:
        if panel_watt <= 0:
            return 0
        return int(ceil(solar_capacity / panel_watt))

    @staticmethod
    def controller_current(solar_capacity: float, system_voltage: float) -> float:
        """Charge controller current in A, with a 25% safety margin."""
        if system_voltage <= 0:
            return 0
        return round((solar_capacity * CONTROLLER_SAFETY_FACTOR) / system_voltage, 2)
