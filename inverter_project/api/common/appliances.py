from collections.abc import Iterable

from power_calculator.models import Appliance

from .exceptions import UnknownApplianceError


def list_appliances() -> list[Appliance]:
    return list(Appliance.objects.only("id", "name"))


def get_appliances_by_ids(ids: Iterable[int]) -> dict[int, Appliance]:
    """Fetch appliances in a single query, raising if any ID is unknown."""
    ids = list(ids)
    appliances = Appliance.objects.in_bulk(ids)
    missing = [appliance_id for appliance_id in ids if appliance_id not in appliances]
    if missing:
        raise UnknownApplianceError(missing)
    return appliances
