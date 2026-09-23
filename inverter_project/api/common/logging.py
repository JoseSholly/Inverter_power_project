"""Exception logging for the Bolt API.

Bolt logs every exception at ERROR with a traceback, including a client's
malformed or invalid request. Those are expected 4xx outcomes, so log them as a
one-line WARNING and keep tracebacks for real server errors (5xx).
"""

import logging
from typing import Any

import msgspec
from django_bolt.exceptions import HTTPException, ValidationException

CLIENT_ERRORS = (ValidationException, msgspec.ValidationError, msgspec.DecodeError)


def is_client_error(exc: Exception) -> bool:
    if isinstance(exc, CLIENT_ERRORS):
        return True
    return isinstance(exc, HTTPException) and exc.status_code < 500


def log_exception(
    logger: logging.Logger, request: dict[str, Any], exc: Exception, exc_info: bool
) -> None:
    method, path = request.get("method", ""), request.get("path", "")
    message = f"{method} {path}: {type(exc).__name__}: {exc}"
    if is_client_error(exc):
        logger.warning("Rejected request %s", message)
    else:
        logger.error("Unhandled exception in %s", message, exc_info=exc_info)
