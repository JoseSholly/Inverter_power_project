"""v2 request/response schemas (HTTP layer only)."""
from typing import Annotated

import msgspec
from msgspec import Meta

from api.common.limits import (
    MAX_APPLIANCE_ID,
    MAX_BACKUP_TIME_H,
    MAX_BATTERY_CAPACITY_AH,
    MAX_ITEMS,
    MAX_POWER_RATING_W,
    MAX_QUANTITY,
    MAX_SOLAR_PANEL_W,
    MAX_SYSTEM_VOLTAGE_V,
)


class ApplianceItemIn(msgspec.Struct):
    id: Annotated[int, Meta(ge=1, le=MAX_APPLIANCE_ID, description="Appliance ID from the appliances endpoint.")]
    quantity: Annotated[int, Meta(ge=1, le=MAX_QUANTITY)]
    power_rating: Annotated[float, Meta(ge=0.01, le=MAX_POWER_RATING_W, description="Power rating in watts (W).")]
    backup_time: Annotated[
        float, Meta(ge=0.01, le=MAX_BACKUP_TIME_H, description="Backup time for this appliance in hours (up to 24).")
    ]


class CalculationIn(msgspec.Struct):
    system_voltage: Annotated[
        float,
        Meta(ge=12, le=MAX_SYSTEM_VOLTAGE_V, multiple_of=12, description="System (battery bank) voltage in V; a multiple of 12 (12V batteries)."),
    ]
    battery_capacity: Annotated[float, Meta(ge=1.0, le=MAX_BATTERY_CAPACITY_AH, description="Capacity of one 12V battery in Ah.")]
    solar_panel_watt: Annotated[float, Meta(ge=1.0, le=MAX_SOLAR_PANEL_W, description="Rating of one solar panel in Wp.")]
    items: Annotated[list[ApplianceItemIn], Meta(min_length=1, max_length=MAX_ITEMS, description="1-100 appliances.")]


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
    total_current: float
    controller_current: float
    items: list[ApplianceItemOut]
