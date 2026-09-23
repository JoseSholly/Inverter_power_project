"""The appliance list endpoint, shared by every API version (same data, same shape).

Responses carry an ETag; a request whose If-None-Match matches gets 304 with no
body. Cache-Control: no-cache lets clients keep the body but makes them
revalidate every time, so they see appliance changes immediately.
"""

import hashlib

from django_bolt.concurrency import sync_to_thread
from django_bolt.responses import Response

from .appliances import list_appliances
from .errors import query_too_long_error
from .limits import MAX_NAME_FILTER_LENGTH

NAME_FILTER_DESCRIPTION = f"Only appliances whose name contains this text (case-insensitive, up to {MAX_NAME_FILTER_LENGTH} characters)."
CACHE_CONTROL = "no-cache"


def _etag(appliances: list[tuple[int, str]]) -> str:
    digest = hashlib.sha256(repr(appliances).encode()).hexdigest()[:32]
    return f'"{digest}"'


def _matches(if_none_match: str | None, etag: str) -> bool:
    if not if_none_match:
        return False
    candidates = {tag.strip().removeprefix("W/") for tag in if_none_match.split(",")}
    return "*" in candidates or etag in candidates


async def list_appliances_response(
    name: str | None, if_none_match: str | None
) -> Response:
    if name is not None and len(name) > MAX_NAME_FILTER_LENGTH:
        raise query_too_long_error("name", name, MAX_NAME_FILTER_LENGTH)
    appliances = await sync_to_thread(list_appliances, name)
    etag = _etag(appliances)
    headers = {"ETag": etag, "Cache-Control": CACHE_CONTROL}
    if _matches(if_none_match, etag):
        return Response(b"", status_code=304, headers=headers)
    return Response([{"id": i, "name": n} for i, n in appliances], headers=headers)
