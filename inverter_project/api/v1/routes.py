"""v1 HTTP routes: translate schemas <-> service DTOs, nothing else."""
from django_bolt import Router
from django_bolt.concurrency import sync_to_thread

from api.common.appliances import list_appliances
from api.common.errors import unknown_appliance_to_validation_error
from api.common.exceptions import UnknownApplianceError
from api.common.schemas import ApplianceOut

from .schemas import ApplianceItemOut, CalculationIn, CalculationOut
from .services import V1CalculationRequest, V1CalculationService, V1ItemRequest

router = Router(tags=["v1"])
calculation_service = V1CalculationService()


@router.get("/appliances/", name="v1-appliances")
async def appliances() -> list[ApplianceOut]:
    """List all appliances that can be referenced by ID in a calculation."""
    return [ApplianceOut(id=a.id, name=a.name) for a in await sync_to_thread(list_appliances)]


@router.post("/calculate/", name="v1-calculate", status_code=200)
async def calculate(data: CalculationIn) -> CalculationOut:
    """
    Size an inverter, battery bank and solar array for a list of appliances.
    A single backup_time applies to every appliance.
    """
    request = V1CalculationRequest(
        backup_time=data.backup_time,
        battery_capacity=data.battery_capacity,
        system_voltage=data.system_voltage,
        solar_panel_watt=data.solar_panel_watt,
        items=tuple(V1ItemRequest(item.id, item.quantity, item.power_rating) for item in data.items),
    )
    try:
        # Services use the sync ORM, so run them off the event loop.
        result = await sync_to_thread(calculation_service.calculate, request)
    except UnknownApplianceError as exc:
        raise unknown_appliance_to_validation_error(exc) from exc

    output = result.output
    return CalculationOut(
        total_load=output.total_load,
        inverter_rating=output.inverter_rating,
        total_battery_capacity=output.total_battery_capacity,
        numbers_of_batteries=output.numbers_of_batteries,
        total_solar_panel_capacity_needed=output.total_solar_panel_capacity_needed,
        numbers_of_solar_panel=output.numbers_of_solar_panel,
        total_current=output.total_current,
        controller_current=output.controller_current,
        backup_time=request.backup_time,
        battery_capacity=request.battery_capacity,
        system_voltage=request.system_voltage,
        solar_panel_watt=request.solar_panel_watt,
        items=[ApplianceItemOut(i.id, i.name, i.quantity, i.power_rating) for i in result.items],
    )
