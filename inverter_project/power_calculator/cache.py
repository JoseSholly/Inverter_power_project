"""Cached appliance catalogue with version-based invalidation.

The whole catalogue (id, name), newest first, lives under one cache key. Every
change bumps a version counter and readers only look at the entry for the
current version. That closes the classic race where a reader loads rows, a
writer invalidates, and the reader then stores the stale rows: the late write
lands under the old version, which nobody reads any more.

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


def _data_key(version: int) -> str:
    return f"appliances:catalog:s{SCHEMA_VERSION}:{version}"


def _timeout() -> int:
    return getattr(settings, "APPLIANCE_CACHE_TIMEOUT", 3600)


def _load_from_db() -> Catalog:
    return tuple(Appliance.objects.values_list("id", "name"))


def _current_version() -> int:
    version = cache.get(VERSION_KEY)
    if version is None:
        # Unknown or evicted: start from a fresh, unique value so entries
        # stored under any earlier version can't be picked up again.
        cache.add(VERSION_KEY, time.time_ns(), timeout=None)
        version = cache.get(VERSION_KEY)
    return version


def get_catalog() -> Catalog:
    """(id, name) for every appliance, newest first."""
    try:
        key = _data_key(_current_version())
        catalog = cache.get(key)
    except Exception:
        logger.warning("Appliance cache unavailable; reading from the database.", exc_info=True)
        return _load_from_db()
    if catalog is not None:
        return catalog

    catalog = _load_from_db()
    try:
        cache.set(key, catalog, timeout=_timeout())
    except Exception:
        logger.warning("Could not store the appliance catalogue in the cache.", exc_info=True)
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
