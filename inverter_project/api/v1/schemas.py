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


_EXAMPLE_ITEMS_IN = [
    {"id": 1, "quantity": 2, "power_rating": 60},
    {"id": 5, "quantity": 1, "power_rating": 900},
]
_EXAMPLE_ITEMS_OUT = [
    {"id": 1, "name": "LED Light", "quantity": 2, "power_rating": 60},
    {"id": 5, "name": "Refrigerator", "quantity": 1, "power_rating": 900},
]


class ApplianceItemIn(msgspec.Struct):
    id: Annotated[
        int,
        Meta(
            ge=1,
            le=MAX_APPLIANCE_ID,
            description="Appliance ID from the appliances endpoint.",
            examples=[1],
        ),
    ]
    quantity: Annotated[int, Meta(ge=1, le=MAX_QUANTITY, examples=[2])] = 1
    power_rating: Annotated[
        int,
        Meta(
            ge=1,
            le=MAX_POWER_RATING_W,
            description="Power rating in watts (W).",
            examples=[60],
        ),
    ] = 1


class CalculationIn(msgspec.Struct):
    backup_time: Annotated[
        int,
        Meta(
            ge=1,
            le=MAX_BACKUP_TIME_H,
            description="Hours of backup needed during an outage (1-24).",
            examples=[8],
        ),
    ]
    battery_capacity: Annotated[
        BatteryCapacity,
        Meta(description="Capacity of one 12V battery in Ah.", examples=[200]),
    ]
    system_voltage: Annotated[
        SystemVoltage,
        Meta(description="System (battery bank) voltage in V.", examples=[24]),
    ]
    solar_panel_watt: Annotated[
        SolarPanelWatt,
        Meta(description="Rating of one solar panel in W.", examples=[400]),
    ]
    items: Annotated[
        list[ApplianceItemIn],
        Meta(
            min_length=1,
            max_length=MAX_ITEMS,
            description="1-100 appliances.",
            examples=[_EXAMPLE_ITEMS_IN],
        ),
    ]


class ApplianceItemOut(msgspec.Struct):
    id: Annotated[int, Meta(examples=[1])]
    name: Annotated[str, Meta(examples=["LED Light"])]
    quantity: Annotated[int, Meta(examples=[2])]
    power_rating: Annotated[int, Meta(examples=[60])]


class CalculationOut(msgspec.Struct):
    total_load: Annotated[int, Meta(examples=[1020])]
    inverter_rating: Annotated[float, Meta(examples=[1275.0])]
    total_battery_capacity: Annotated[float, Meta(examples=[425.0])]
    numbers_of_batteries: Annotated[int, Meta(examples=[2])]
    total_solar_panel_capacity_needed: Annotated[float, Meta(examples=[1600.0])]
    numbers_of_solar_panel: Annotated[int, Meta(examples=[4])]
    total_current: Annotated[float, Meta(examples=[42.5])]
    controller_current: Annotated[float, Meta(examples=[53.13])]
    backup_time: Annotated[int, Meta(examples=[8])]
    battery_capacity: Annotated[int, Meta(examples=[200])]
    system_voltage: Annotated[int, Meta(examples=[24])]
    solar_panel_watt: Annotated[int, Meta(examples=[400])]
    items: Annotated[list[ApplianceItemOut], Meta(examples=[_EXAMPLE_ITEMS_OUT])]


# Version-prefix the OpenAPI titles so Swagger UI doesn't dedupe v1/v2 schemas
# by their short class name (which collapses each endpoint's example onto the
# other's shape).
for _cls in (ApplianceItemIn, CalculationIn, ApplianceItemOut, CalculationOut):
    _cls.__name__ = f"V1{_cls.__name__}"
    _cls.__qualname__ = _cls.__name__
del _cls
