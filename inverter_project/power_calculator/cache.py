"""Cached appliance catalogue with version-based invalidation.

The whole catalogue (id, name), sorted alphabetically by name, lives under one
cache key. Every change bumps a version counter and readers only look at the
entry for the current version. That closes the classic race where a reader
loads rows, a writer invalidates, and the reader then stores the stale rows:
the late write lands under the old version, which nobody reads any more.

If the cache backend fails (e.g. Redis is down) we log a warning and use the
database directly; caching must never turn into a 500.
"""

import logging
import time

from django.conf import settings
from django.core.cache import cache
from django.db import transaction

from .models import Appliance

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1
"""Bump when the cached value's shape changes so old entries are ignored."""

VERSION_KEY = "appliances:catalog:version"

Catalog = tuple[tuple[int, str], ...]

_last_version = 0
"""Process-local floor so re-created version keys never reuse an old id."""


def _data_key(version: int) -> str:
    return f"appliances:catalog:s{SCHEMA_VERSION}:{version}"


def _timeout() -> int:
    return getattr(settings, "APPLIANCE_CACHE_TIMEOUT", 3600)


def _load_from_db() -> Catalog:
    rows = Appliance.objects.values_list("id", "name")
    return tuple(sorted(rows, key=lambda row: row[1].casefold()))


def _current_version() -> int:
    global _last_version
    version = cache.get(VERSION_KEY)
    if version is None:
        # Unknown or evicted: start from a fresh, unique value so entries
        # stored under any earlier version can't be picked up again.
        # time.time_ns() can repeat on coarse timers (Windows), so also keep
        # a process-local floor that only moves forward.
        _last_version = max(time.time_ns(), _last_version + 1)
        cache.add(VERSION_KEY, _last_version, timeout=None)
        version = cache.get(VERSION_KEY)
    elif version > _last_version:
        _last_version = version
    return version


def get_catalog() -> Catalog:
    """(id, name) for every appliance, alphabetically by name."""
    try:
        key = _data_key(_current_version())
        catalog = cache.get(key)
    except Exception:
        logger.warning(
            "Appliance cache unavailable; reading from the database.", exc_info=True
        )
        return _load_from_db()
    if catalog is not None:
        return catalog

    catalog = _load_from_db()
    try:
        cache.set(key, catalog, timeout=_timeout())
    except Exception:
        logger.warning(
            "Could not store the appliance catalogue in the cache.", exc_info=True
        )
    return catalog


def invalidate() -> None:
    """Make every process re-read appliances from the database on next use."""
    try:
        cache.incr(VERSION_KEY)
    except ValueError:
        pass  # no version yet: the next reader starts a fresh one
    except Exception:
        logger.warning("Could not invalidate the appliance cache.", exc_info=True)


def invalidate_now_and_on_commit() -> None:
    """Invalidate immediately and again once the transaction commits.

    The first bump hides the old catalogue at once; the second one discards
    anything a concurrent reader cached from pre-commit data in between.
    """
    invalidate()
    transaction.on_commit(invalidate)
