from collections.abc import Sequence

from django_bolt.exceptions import RequestValidationError

from .exceptions import UnknownApplianceError


def unknown_appliance_to_validation_error(
    exc: UnknownApplianceError, requested_ids: Sequence[int]
) -> RequestValidationError:
    """Translate the domain error into Bolt's 422 format, one error per offending item
    (loc points at the item's index, like Bolt's own validation errors)."""
    missing = set(exc.missing_ids)
    return RequestValidationError(
        [
            {
                "type": "unknown_appliance",
                "loc": ["body", "items", str(index), "id"],
                "msg": f"Appliance with ID {appliance_id} does not exist.",
                "input": appliance_id,
            }
            for index, appliance_id in enumerate(requested_ids)
            if appliance_id in missing
        ]
    )
