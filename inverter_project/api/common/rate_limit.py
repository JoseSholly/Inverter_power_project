"""Per-client rate limit shared by every endpoint (django-bolt's built-in limiter).

A token bucket keyed on the client IP: `RATE_LIMIT_RPS` requests per second on
average, with bursts up to `RATE_LIMIT_BURST`. Over the limit gets a 429.
Set `RATE_LIMIT_RPS=0` to turn it off (e.g. for load tests).

Behind a proxy (Render, Vercel) every caller shares the proxy's IP unless the
proxy is listed in `BOLT_TRUSTED_PROXIES`; see the README.
"""

from django.conf import settings
from django_bolt.middleware import rate_limit


def limited(handler):
    """Decorator for route handlers. Apply it *below* the route decorator."""
    if settings.RATE_LIMIT_RPS <= 0:
        return handler
    return rate_limit(
        rps=settings.RATE_LIMIT_RPS,
        burst=settings.RATE_LIMIT_BURST,
        key="ip",
    )(handler)
