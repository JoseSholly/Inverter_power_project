"""v2 HTTP routes: translate schemas <-> service DTOs, nothing else."""

from typing import Annotated

from django_bolt import Router
from django_bolt.concurrency import sync_to_thread
from django_bolt.params import Header, Query
from django_bolt.responses import Response

from api.common.appliance_endpoint import (
    NAME_FILTER_DESCRIPTION,
    list_appliances_response,
)
from api.common.errors import unknown_appliance_to_validation_error
from api.common.exceptions import UnknownApplianceError
from api.common.routing import Routes
from api.common.schemas import ApplianceOut

from .schemas import V2ApplianceItemOut, V2CalculationIn, V2CalculationOut
from .services import V2CalculationRequest, V2CalculationService, V2ItemRequest

routes = Routes(Router(tags=["v2"]))
calculation_service = V2CalculationService()


@routes.get("/appliances/", name="v2-appliances", response_model=list[ApplianceOut])
async def v2_appliances(
    name: Annotated[str | None, Query(description=NAME_FILTER_DESCRIPTION)] = None,
    if_none_match: Annotated[str | None, Header(alias="If-None-Match")] = None,
) -> Response:
    """List appliances that can be referenced by ID in a calculation, optionally filtered by name."""
    return await list_appliances_response(name, if_none_match)


@routes.post("/calculate/", name="v2-calculate", status_code=200)
async def v2_calculate(data: V2CalculationIn) -> V2CalculationOut:
    """
    Size an inverter, battery bank and solar array for a list of appliances.
    Each appliance has its own backup_time. Nothing is stored.
    """
    request = V2CalculationRequest(
        system_voltage=data.system_voltage,
        battery_capacity=data.battery_capacity,
        solar_panel_watt=data.solar_panel_watt,
        items=tuple(
            V2ItemRequest(item.id, item.quantity, item.power_rating, item.backup_time)
            for item in data.items
        ),
    )
    try:
        # Services use the sync ORM, so run them off the event loop.
        result = await sync_to_thread(calculation_service.calculate, request)
    except UnknownApplianceError as exc:
        raise unknown_appliance_to_validation_error(
            exc, [item.id for item in data.items]
        ) from exc

    output = result.output
    return V2CalculationOut(
        system_voltage=request.system_voltage,
        battery_capacity=request.battery_capacity,
        solar_panel_watt=request.solar_panel_watt,
        total_load=output.total_load,
        inverter_rating=output.inverter_rating,
        total_battery_capacity=output.total_battery_capacity,
        numbers_of_batteries=output.numbers_of_batteries,
        total_solar_panel_capacity_needed=output.total_solar_panel_capacity_needed,
        numbers_of_solar_panel=output.numbers_of_solar_panel,
        total_current=output.total_current,
        controller_current=output.controller_current,
        items=[
            V2ApplianceItemOut(i.id, i.name, i.quantity, i.power_rating, i.backup_time)
            for i in result.items
        ],
    )


router = routes.finalize()
