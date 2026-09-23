"""Appliance lookups for the API, served from the cached catalogue
(power_calculator/cache.py), so warm requests don't touch the database."""
from collections.abc import Iterable

from power_calculator.cache import get_catalog

from .exceptions import UnknownApplianceError


def _normalize(text: str) -> str:
    return " ".join(text.split()).casefold()


def list_appliances(name: str | None = None) -> list[tuple[int, str]]:
    """(id, name) for every appliance, newest first; `name` keeps those whose
    name contains it (case-insensitive, whitespace-trimmed). Blank means no filter.

    Matching uses casefold() in Python rather than SQL icontains, whose case
    folding differs between databases (SQLite only folds ASCII).
    """
    catalog = get_catalog()
    needle = _normalize(name or "")
    if not needle:
        return list(catalog)
    return [(appliance_id, appliance_name) for appliance_id, appliance_name in catalog
            if needle in _normalize(appliance_name)]


def get_appliance_names(ids: Iterable[int]) -> dict[int, str]:
    """Names for the given appliance IDs, raising if any ID is unknown."""
    ids = list(ids)
    names = dict(get_catalog())
    missing = [appliance_id for appliance_id in ids if appliance_id not in names]
    if missing:
        raise UnknownApplianceError(missing)
    return {appliance_id: names[appliance_id] for appliance_id in ids}
