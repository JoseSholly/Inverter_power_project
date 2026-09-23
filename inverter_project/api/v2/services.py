"""v2 calculation service: resolves appliances and runs the v2 calculator."""
from dataclasses import dataclass

from api.common.appliances import get_appliance_names

from .calculator import LoadItem, V2CalculationInput, V2CalculationOutput, V2Calculator


@dataclass(frozen=True)
class V2ItemRequest:
    appliance_id: int
    quantity: int
    power_rating: float
    backup_time: float


@dataclass(frozen=True)
class V2CalculationRequest:
    system_voltage: float
    battery_capacity: float
    solar_panel_watt: float
    items: tuple[V2ItemRequest, ...]


@dataclass(frozen=True)
class V2ResolvedItem:
    id: int
    name: str
    quantity: int
    power_rating: float
    backup_time: float


@dataclass(frozen=True)
class V2CalculationResult:
    request: V2CalculationRequest
    output: V2CalculationOutput
    items: tuple[V2ResolvedItem, ...]


class V2CalculationService:
    def __init__(self, calculator: V2Calculator | None = None):
        self.calculator = calculator or V2Calculator()

    def calculate(self, request: V2CalculationRequest) -> V2CalculationResult:
        names = get_appliance_names(item.appliance_id for item in request.items)
        output = self.calculator.calculate(
            V2CalculationInput(
                battery_capacity=request.battery_capacity,
                system_voltage=request.system_voltage,
                solar_panel_watt=request.solar_panel_watt,
                items=tuple(
                    LoadItem(item.quantity, item.power_rating, item.backup_time) for item in request.items
                ),
            )
        )
        items = tuple(
            V2ResolvedItem(
                id=item.appliance_id,
                name=names[item.appliance_id],
                quantity=item.quantity,
                power_rating=item.power_rating,
                backup_time=item.backup_time,
            )
            for item in request.items
        )
        return V2CalculationResult(request=request, output=output, items=items)
