"""v1 request/response schemas (HTTP layer only)."""
from typing import Annotated, Literal

import msgspec
from msgspec import Meta

from api.common.limits import (
    MAX_APPLIANCE_ID,
    MAX_BACKUP_TIME_H,
    MAX_ITEMS,
    MAX_POWER_RATING_W,
    MAX_QUANTITY,
)

BatteryCapacity = Literal[150, 200, 220, 250]
SystemVoltage = Literal[12, 24, 48]
SolarPanelWatt = Literal[300, 350, 400, 450]


class ApplianceItemIn(msgspec.Struct):
    id: Annotated[int, Meta(ge=1, le=MAX_APPLIANCE_ID, description="Appliance ID from the appliances endpoint.")]
    quantity: Annotated[int, Meta(ge=1, le=MAX_QUANTITY)] = 1
    power_rating: Annotated[int, Meta(ge=1, le=MAX_POWER_RATING_W, description="Power rating in watts (W).")] = 1


class CalculationIn(msgspec.Struct):
    backup_time: Annotated[
        int, Meta(ge=1, le=MAX_BACKUP_TIME_H, description="Hours of backup needed during an outage (1-24).")
    ]
    battery_capacity: Annotated[BatteryCapacity, Meta(description="Capacity of one 12V battery in Ah.")]
    system_voltage: Annotated[SystemVoltage, Meta(description="System (battery bank) voltage in V.")]
    solar_panel_watt: Annotated[SolarPanelWatt, Meta(description="Rating of one solar panel in W.")]
    items: Annotated[list[ApplianceItemIn], Meta(min_length=1, max_length=MAX_ITEMS, description="1-100 appliances.")]


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
    controller_current: float
    backup_time: int
    battery_capacity: int
    system_voltage: int
    solar_panel_watt: int
    items: list[ApplianceItemOut]
