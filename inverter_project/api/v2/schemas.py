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

_EXAMPLE_ITEMS_IN = [
    {"id": 1, "quantity": 2, "power_rating": 60.0, "backup_time": 8.0},
    {"id": 5, "quantity": 1, "power_rating": 900.0, "backup_time": 4.0},
]
_EXAMPLE_ITEMS_OUT = [
    {
        "id": 1,
        "name": "LED Light",
        "quantity": 2,
        "power_rating": 60.0,
        "backup_time": 8.0,
    },
    {
        "id": 5,
        "name": "Refrigerator",
        "quantity": 1,
        "power_rating": 900.0,
        "backup_time": 4.0,
    },
]


class V2ApplianceItemIn(msgspec.Struct):
    id: Annotated[
        int,
        Meta(
            ge=1,
            le=MAX_APPLIANCE_ID,
            description="Appliance ID from the appliances endpoint.",
            examples=[1],
        ),
    ]
    quantity: Annotated[int, Meta(ge=1, le=MAX_QUANTITY, examples=[2])]
    power_rating: Annotated[
        float,
        Meta(
            ge=0.01,
            le=MAX_POWER_RATING_W,
            description="Power rating in watts (W).",
            examples=[60.0],
        ),
    ]
    backup_time: Annotated[
        float,
        Meta(
            ge=0.01,
            le=MAX_BACKUP_TIME_H,
            description="Backup time for this appliance in hours (up to 24).",
            examples=[8.0],
        ),
    ]


class V2CalculationIn(msgspec.Struct):
    system_voltage: Annotated[
        float,
        Meta(
            ge=12,
            le=MAX_SYSTEM_VOLTAGE_V,
            multiple_of=12,
            description="System (battery bank) voltage in V; a multiple of 12 (12V batteries).",
            examples=[24],
        ),
    ]
    battery_capacity: Annotated[
        float,
        Meta(
            ge=1.0,
            le=MAX_BATTERY_CAPACITY_AH,
            description="Capacity of one 12V battery in Ah.",
            examples=[200],
        ),
    ]
    solar_panel_watt: Annotated[
        float,
        Meta(
            ge=1.0,
            le=MAX_SOLAR_PANEL_W,
            description="Rating of one solar panel in Wp.",
            examples=[400],
        ),
    ]
    items: Annotated[
        list[V2ApplianceItemIn],
        Meta(
            min_length=1,
            max_length=MAX_ITEMS,
            description="1-100 appliances.",
            examples=[_EXAMPLE_ITEMS_IN],
        ),
    ]


class V2ApplianceItemOut(msgspec.Struct):
    id: Annotated[int, Meta(examples=[1])]
    name: Annotated[str, Meta(examples=["LED Light"])]
    quantity: Annotated[int, Meta(examples=[2])]
    power_rating: Annotated[float, Meta(examples=[60.0])]
    backup_time: Annotated[float, Meta(examples=[8.0])]


class V2CalculationOut(msgspec.Struct):
    system_voltage: Annotated[float, Meta(examples=[24])]
    battery_capacity: Annotated[float, Meta(examples=[200])]
    solar_panel_watt: Annotated[float, Meta(examples=[400])]
    total_load: Annotated[float, Meta(examples=[1020.0])]
    inverter_rating: Annotated[float, Meta(examples=[1275.0])]
    total_battery_capacity: Annotated[float, Meta(examples=[190.0])]
    numbers_of_batteries: Annotated[int, Meta(examples=[2])]
    total_solar_panel_capacity_needed: Annotated[float, Meta(examples=[1200.0])]
    numbers_of_solar_panel: Annotated[int, Meta(examples=[3])]
    total_current: Annotated[float, Meta(examples=[42.5])]
    controller_current: Annotated[float, Meta(examples=[53.13])]
    items: Annotated[list[V2ApplianceItemOut], Meta(examples=[_EXAMPLE_ITEMS_OUT])]
