"""v1 request/response schemas (HTTP layer only)."""
from typing import Annotated, Literal

import msgspec
from msgspec import Meta

BatteryCapacity = Literal[150, 200, 220, 250]
SystemVoltage = Literal[12, 24, 48]
SolarPanelWatt = Literal[300, 350, 400, 450]


class ApplianceItemIn(msgspec.Struct):
    id: Annotated[int, Meta(ge=1, description="Appliance ID from the appliances endpoint.")]
    quantity: Annotated[int, Meta(ge=1)] = 1
    power_rating: Annotated[int, Meta(ge=1, description="Power rating in watts (W).")] = 1


class CalculationIn(msgspec.Struct):
    backup_time: Annotated[int, Meta(ge=1, description="How many hours of backup you need during a power outage.")]
    battery_capacity: Annotated[BatteryCapacity, Meta(description="Capacity of one 12V battery in Ah.")]
    system_voltage: Annotated[SystemVoltage, Meta(description="System (battery bank) voltage in V.")]
    solar_panel_watt: Annotated[SolarPanelWatt, Meta(description="Rating of one solar panel in W.")]
    items: list[ApplianceItemIn]


class ApplianceItemOut(msgspec.Struct):
    id: int
    name: str
    quantity: int
    power_rating: int


class CalculationOut(msgspec.Struct):
    total_load: int
    inverter_rating: float
    total_battery_capacity: float
    numbers_of_batteries: int
    total_solar_panel_capacity_needed: float
    numbers_of_solar_panel: int
    total_current: float
    backup_time: int
    battery_capacity: int
    system_voltage: int
    solar_panel_watt: int
    items: list[ApplianceItemOut]
