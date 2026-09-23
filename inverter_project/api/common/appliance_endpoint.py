"""The appliance list endpoint, shared by every API version (same data, same shape)."""
from django_bolt.concurrency import sync_to_thread

from .appliances import list_appliances
from .errors import query_too_long_error
from .limits import MAX_NAME_FILTER_LENGTH
from .schemas import ApplianceOut

NAME_FILTER_DESCRIPTION = (
    f"Only appliances whose name contains this text (case-insensitive, up to {MAX_NAME_FILTER_LENGTH} characters)."
)


async def list_appliances_response(name: str | None) -> list[ApplianceOut]:
    if name is not None and len(name) > MAX_NAME_FILTER_LENGTH:
        raise query_too_long_error("name", name, MAX_NAME_FILTER_LENGTH)
    appliances = await sync_to_thread(list_appliances, name)
    return [ApplianceOut(id=a.id, name=a.name) for a in appliances]
