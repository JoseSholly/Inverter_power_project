from django_bolt.exceptions import RequestValidationError

from .exceptions import UnknownApplianceError


def unknown_appliance_to_validation_error(exc: UnknownApplianceError) -> RequestValidationError:
    """Translate the domain error into Bolt's 422 validation error."""
    return RequestValidationError(
        [
            {
                "type": "unknown_appliance",
                "loc": ["body", "items", "id"],
                "msg": str(exc),
                "input": exc.missing_ids,
            }
        ]
    )
