"""v1 sizing: one backup time shared by every appliance.

Energy = total load x backup time; everything after that uses the shared
sizing model in api/common/sizing.py. Pure Python, no Django or HTTP imports.
"""

from dataclasses import dataclass

from api.common import sizing


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
    controller_current: float


class V1Calculator:
    def calculate(self, data: V1CalculationInput) -> V1CalculationOutput:
        total_load = self.total_load(data.items)
        energy = self.energy(total_load, data.backup_time)
        bank_capacity = sizing.battery_capacity_ah(energy, data.system_voltage)
        array_capacity = sizing.solar_array_capacity_wp(energy)
        panels = sizing.number_of_panels(array_capacity, data.solar_panel_watt)
        return V1CalculationOutput(
            total_load=total_load,
            inverter_rating=sizing.inverter_rating_kva(total_load),
            total_battery_capacity=bank_capacity,
            numbers_of_batteries=sizing.number_of_batteries(
                bank_capacity, data.battery_capacity, data.system_voltage
            ),
            total_solar_panel_capacity_needed=array_capacity,
            numbers_of_solar_panel=panels,
            total_current=sizing.array_current_a(
                panels, data.solar_panel_watt, data.system_voltage
            ),
            controller_current=sizing.controller_current_a(
                panels, data.solar_panel_watt, data.system_voltage
            ),
        )

    @staticmethod
    def total_load(items: tuple[LoadItem, ...]) -> int:
        """Total power draw in W."""
        return sum(item.power_rating * item.quantity for item in items)

    @staticmethod
    def energy(total_load: float, backup_time: float) -> float:
        """Energy needed in Wh: every appliance runs for the same backup time."""
        return total_load * backup_time
