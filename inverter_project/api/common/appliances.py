from collections.abc import Iterable

from power_calculator.models import Appliance

from .exceptions import UnknownApplianceError


def _normalize(text: str) -> str:
    return " ".join(text.split()).casefold()


def list_appliances(name: str | None = None) -> list[Appliance]:
    """All appliances, newest first; `name` keeps those whose name contains it
    (case-insensitive, whitespace-trimmed). A blank `name` means no filter.

    Matching uses casefold() in Python rather than SQL icontains, whose case
    folding differs between databases (SQLite only folds ASCII).
    """
    appliances = list(Appliance.objects.only("id", "name"))
    needle = _normalize(name or "")
    if not needle:
        return appliances
    return [a for a in appliances if needle in _normalize(a.name)]


def get_appliances_by_ids(ids: Iterable[int]) -> dict[int, Appliance]:
    """Fetch appliances in a single query, raising if any ID is unknown."""
    ids = list(ids)
    appliances = Appliance.objects.in_bulk(ids)
    missing = [appliance_id for appliance_id in ids if appliance_id not in appliances]
    if missing:
        raise UnknownApplianceError(missing)
    return appliances
