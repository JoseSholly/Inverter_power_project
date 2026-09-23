from io import StringIO
from unittest import mock

from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings

from power_calculator import cache as appliance_cache
from power_calculator.models import Appliance

LOCMEM = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "cache-tests",
    }
}


@override_settings(CACHES=LOCMEM)
class ApplianceCacheTests(TestCase):
    def setUp(self):
        cache.clear()
        self.fan = Appliance.objects.create(name="Fan")
        self.tv = Appliance.objects.create(name="TV")

    def test_warm_reads_hit_no_database(self):
        with self.assertNumQueries(1):
            first = appliance_cache.get_catalog()
        with self.assertNumQueries(0):
            second = appliance_cache.get_catalog()
        self.assertEqual(first, second)
        self.assertEqual(
            first, ((self.fan.id, "Fan"), (self.tv.id, "TV"))
        )  # alphabetical

    def test_create_rename_and_delete_invalidate(self):
        appliance_cache.get_catalog()
        heater = Appliance.objects.create(name="Heater")
        self.assertIn((heater.id, "Heater"), appliance_cache.get_catalog())

        heater.name = "Water Heater"
        heater.save()
        self.assertIn((heater.id, "Water Heater"), appliance_cache.get_catalog())

        heater.delete()
        self.assertNotIn(heater.id, dict(appliance_cache.get_catalog()))

    def test_queryset_delete_invalidates(self):
        # The admin's "delete selected" action uses QuerySet.delete(), which sends post_delete per row.
        appliance_cache.get_catalog()
        Appliance.objects.filter(name="TV").delete()
        self.assertEqual(dict(appliance_cache.get_catalog()), {self.fan.id: "Fan"})

    def test_invalidates_again_on_commit(self):
        appliance_cache.get_catalog()
        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            Appliance.objects.create(name="Kettle")
        self.assertEqual(len(callbacks), 1)
        version = cache.get(appliance_cache.VERSION_KEY)
        callbacks[0]()
        self.assertEqual(cache.get(appliance_cache.VERSION_KEY), version + 1)

    def test_stale_write_from_a_slow_reader_is_never_served(self):
        """Reader loads rows, a writer changes data, then the reader stores its stale rows."""
        real_load = appliance_cache._load_from_db
        state = {}

        def slow_load():
            rows = real_load()  # reader has the old rows...
            if not state:
                state["kettle"] = Appliance.objects.create(
                    name="Kettle"
                )  # ...a write lands...
            return rows  # ...and the reader stores stale data

        with mock.patch.object(appliance_cache, "_load_from_db", side_effect=slow_load):
            stale = appliance_cache.get_catalog()
        self.assertNotIn(state["kettle"].id, dict(stale))
        self.assertIn(state["kettle"].id, dict(appliance_cache.get_catalog()))

    def test_bulk_changes_need_clear_appliance_cache(self):
        appliance_cache.get_catalog()
        Appliance.objects.filter(id=self.tv.id).update(name="Television")  # no signals
        self.assertEqual(dict(appliance_cache.get_catalog())[self.tv.id], "TV")
        out = StringIO()
        call_command("clear_appliance_cache", stdout=out)
        self.assertIn("invalidated", out.getvalue())
        self.assertEqual(dict(appliance_cache.get_catalog())[self.tv.id], "Television")

    def test_populate_appliances_invalidates(self):
        appliance_cache.get_catalog()
        call_command("populate_appliances", stdout=StringIO())
        self.assertIn("LED Light", dict(appliance_cache.get_catalog()).values())

    def test_evicted_version_key_does_not_resurrect_old_entries(self):
        appliance_cache.get_catalog()
        Appliance.objects.filter(id=self.tv.id).update(name="Television")
        cache.delete(appliance_cache.VERSION_KEY)  # e.g. evicted by Redis
        self.assertEqual(dict(appliance_cache.get_catalog())[self.tv.id], "Television")

    def test_cache_backend_failure_falls_back_to_database(self):
        with (
            mock.patch.object(
                appliance_cache.cache, "get", side_effect=ConnectionError("redis down")
            ),
            self.assertLogs("power_calculator.cache", level="WARNING"),
        ):
            catalog = appliance_cache.get_catalog()
        self.assertEqual(dict(catalog), {self.fan.id: "Fan", self.tv.id: "TV"})

    def test_invalidate_survives_backend_failure(self):
        with (
            mock.patch.object(
                appliance_cache.cache, "incr", side_effect=ConnectionError("redis down")
            ),
            self.assertLogs("power_calculator.cache", level="WARNING"),
        ):
            appliance_cache.invalidate()
