from django.test.runner import DiscoverRunner
from django.test.utils import override_settings

DUMMY_CACHE = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}


class CacheIsolatingTestRunner(DiscoverRunner):
    """Run the suite with a no-op cache.

    TestCase rolls the database back after every test but never clears the
    cache, so cached rows from one test would leak into the next. Tests that
    exercise caching opt back in with @override_settings(CACHES=...) and clear
    the cache in setUp.
    """

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self._cache_override = override_settings(CACHES=DUMMY_CACHE)
        self._cache_override.enable()

    def teardown_test_environment(self, **kwargs):
        self._cache_override.disable()
        super().teardown_test_environment(**kwargs)
