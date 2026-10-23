from django.test.runner import DiscoverRunner
from django.test.utils import override_settings

DUMMY_CACHE = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}


class CacheIsolatingTestRunner(DiscoverRunner):
    """Run the suite with a no-op cache and no rate limit.

    The rate limiter keeps one process-wide bucket per IP, so with it on the
    suite would start failing with 429s depending on test order. It is turned
    off before the routes are imported; the rate-limit test builds its own tiny
    app with the limit switched on.

    TestCase rolls the database back after every test but never clears the
    cache, so cached rows from one test would leak into the next. Tests that
    exercise caching opt back in with @override_settings(CACHES=...) and clear
    the cache in setUp.
    """

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self._cache_override = override_settings(CACHES=DUMMY_CACHE, RATE_LIMIT_RPS=0)
        self._cache_override.enable()

    def teardown_test_environment(self, **kwargs):
        self._cache_override.disable()
        super().teardown_test_environment(**kwargs)
