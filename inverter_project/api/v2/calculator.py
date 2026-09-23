"""v2 sizing: every appliance has its own backup time.

Energy = sum(power x quantity x backup time); everything after that uses the
shared sizing model in api/common/sizing.py. Pure Python, no Django or HTTP imports.
"""
from dataclasses import dataclass

from api.common import sizing


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
    total_current: float
    controller_current: float


class V2Calculator:
    def calculate(self, data: V2CalculationInput) -> V2CalculationOutput:
        total_load = self.total_load(data.items)
        energy = self.energy(data.items)
        bank_capacity = sizing.battery_capacity_ah(energy, data.system_voltage)
        array_capacity = sizing.solar_array_capacity_wp(energy)
        panels = sizing.number_of_panels(array_capacity, data.solar_panel_watt)
        return V2CalculationOutput(
            total_load=total_load,
            inverter_rating=sizing.inverter_rating_kva(total_load),
            total_battery_capacity=bank_capacity,
            numbers_of_batteries=sizing.number_of_batteries(
                bank_capacity, data.battery_capacity, data.system_voltage
            ),
            total_solar_panel_capacity_needed=array_capacity,
            numbers_of_solar_panel=panels,
            total_current=sizing.array_current_a(panels, data.solar_panel_watt, data.system_voltage),
            controller_current=sizing.controller_current_a(panels, data.solar_panel_watt, data.system_voltage),
        )

    @staticmethod
    def total_load(items: tuple[LoadItem, ...]) -> float:
        """Total power draw in W."""
        return round(sum(item.power for item in items), 2)

    @staticmethod
    def energy(items: tuple[LoadItem, ...]) -> float:
        """Energy needed in Wh: each appliance runs for its own backup time."""
        return sum(item.energy for item in items)
