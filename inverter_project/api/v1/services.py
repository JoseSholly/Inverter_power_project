"""v1 calculation service: resolves appliances and runs the v1 calculator."""
from dataclasses import dataclass

from api.common.appliances import get_appliances_by_ids

from .calculator import LoadItem, V1CalculationInput, V1CalculationOutput, V1Calculator


@dataclass(frozen=True)
class V1ItemRequest:
    appliance_id: int
    quantity: int
    power_rating: int


@dataclass(frozen=True)
class V1CalculationRequest:
    backup_time: int
    battery_capacity: int
    system_voltage: int
    solar_panel_watt: int
    items: tuple[V1ItemRequest, ...]


@dataclass(frozen=True)
class V1ResolvedItem:
    id: int
    name: str
    quantity: int
    power_rating: int


@dataclass(frozen=True)
class V1CalculationResult:
    request: V1CalculationRequest
    output: V1CalculationOutput
    items: tuple[V1ResolvedItem, ...]


class V1CalculationService:
    def __init__(self, calculator: V1Calculator | None = None):
        self.calculator = calculator or V1Calculator()

    def calculate(self, request: V1CalculationRequest) -> V1CalculationResult:
        appliances = get_appliances_by_ids(item.appliance_id for item in request.items)
        output = self.calculator.calculate(
            V1CalculationInput(
                backup_time=request.backup_time,
                battery_capacity=request.battery_capacity,
                system_voltage=request.system_voltage,
                solar_panel_watt=request.solar_panel_watt,
                items=tuple(LoadItem(item.quantity, item.power_rating) for item in request.items),
            )
        )
        items = tuple(
            V1ResolvedItem(
                id=item.appliance_id,
                name=appliances[item.appliance_id].name,
                quantity=item.quantity,
                power_rating=item.power_rating,
            )
            for item in request.items
        )
        return V1CalculationResult(request=request, output=output, items=items)
