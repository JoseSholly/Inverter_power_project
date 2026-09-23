"""v2 request/response schemas (HTTP layer only)."""
from typing import Annotated

import msgspec
from msgspec import Meta


class ApplianceItemIn(msgspec.Struct):
    id: Annotated[int, Meta(ge=1, description="Appliance ID from the appliances endpoint.")]
    quantity: Annotated[int, Meta(ge=1)]
    power_rating: Annotated[float, Meta(ge=0.01, description="Power rating in watts (W).")]
    backup_time: Annotated[float, Meta(ge=0.01, description="Backup time for this appliance in hours.")]


class CalculationIn(msgspec.Struct):
    system_voltage: Annotated[float, Meta(ge=1.0, description="System (battery bank) voltage in V.")]
    battery_capacity: Annotated[float, Meta(ge=1.0, description="Capacity of one 12V battery in Ah.")]
    solar_panel_watt: Annotated[float, Meta(ge=1.0, description="Rating of one solar panel in Wp.")]
    items: Annotated[list[ApplianceItemIn], Meta(min_length=1, description="At least one appliance.")]


class ApplianceItemOut(msgspec.Struct):
    id: int
    name: str
    quantity: int
    power_rating: float
    backup_time: float


class CalculationOut(msgspec.Struct):
    system_voltage: float
    battery_capacity: float
    solar_panel_watt: float
    total_load: float
    inverter_rating: float
    total_battery_capacity: float
    numbers_of_batteries: int
    total_solar_panel_capacity_needed: float
    numbers_of_solar_panel: int
    controller_current: float
    items: list[ApplianceItemOut]
