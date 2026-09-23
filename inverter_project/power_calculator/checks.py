from django.conf import settings
from django.core.checks import Warning, register


@register(deploy=True)
def shared_cache_check(app_configs, **kwargs):
    """Appliance cache invalidation only reaches every server process with a shared cache."""
    backend = settings.CACHES.get("default", {}).get("BACKEND", "")
    if backend.endswith(("LocMemCache", "DummyCache")):
        return [
            Warning(
                "The default cache is per-process, so appliance cache invalidation won't reach "
                "other runbolt processes.",
                hint="Set REDIS_URL, or run a single process.",
                id="power_calculator.W001",
            )
        ]
    return []
