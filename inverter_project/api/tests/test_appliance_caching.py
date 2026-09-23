from unittest import mock

from django.core.cache import cache
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django_bolt.testing import TestClient

from inverter_project.api import api
from power_calculator import cache as appliance_cache
from power_calculator.models import Appliance

LOCMEM = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "api-cache-tests",
    }
}
LIST_URL = "/api/v1/power_calculator/appliances/"


@override_settings(CACHES=LOCMEM)
class ApplianceCachingEndpointTests(TestCase):
    def setUp(self):
        cache.clear()
        self.fan = Appliance.objects.create(name="Fan")
        self.client = TestClient(api)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def test_warm_list_and_calculations_make_no_queries(self):
        self.client.get(LIST_URL)  # warm the cache
        payloads = [
            (
                "/api/v1/power_calculator/calculate/",
                {
                    "backup_time": 2,
                    "battery_capacity": 200,
                    "system_voltage": 12,
                    "solar_panel_watt": 300,
                    "items": [{"id": self.fan.id}],
                },
            ),
            (
                "/api/v2/power_calculator/calculate/",
                {
                    "system_voltage": 12,
                    "battery_capacity": 200,
                    "solar_panel_watt": 300,
                    "items": [
                        {
                            "id": self.fan.id,
                            "quantity": 1,
                            "power_rating": 75,
                            "backup_time": 2,
                        }
                    ],
                },
            ),
        ]
        with CaptureQueriesContext(connection) as queries:
            self.assertEqual(self.client.get(LIST_URL).status_code, 200)
            self.assertEqual(
                self.client.get(
                    "/api/v2/power_calculator/appliances/?name=fa"
                ).status_code,
                200,
            )
            for url, body in payloads:
                self.assertEqual(self.client.post(url, json=body).status_code, 200)
        self.assertEqual(len(queries), 0, [q["sql"] for q in queries])

    def test_changes_show_up_immediately(self):
        self.assertEqual([a["name"] for a in self.client.get(LIST_URL).json()], ["Fan"])
        self.fan.name = "Ceiling Fan"
        self.fan.save()
        self.assertEqual(
            [a["name"] for a in self.client.get(LIST_URL).json()], ["Ceiling Fan"]
        )
        self.fan.delete()
        self.assertEqual(self.client.get(LIST_URL).json(), [])

    def test_calculation_sees_new_appliance_without_waiting(self):
        self.client.get(LIST_URL)
        kettle = Appliance.objects.create(name="Kettle")
        body = {
            "backup_time": 1,
            "battery_capacity": 200,
            "system_voltage": 12,
            "solar_panel_watt": 300,
            "items": [{"id": kettle.id}],
        }
        response = self.client.post("/api/v1/power_calculator/calculate/", json=body)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"][0]["name"], "Kettle")

    def test_etag_and_conditional_requests(self):
        response = self.client.get(LIST_URL)
        etag = response.headers["etag"]
        self.assertEqual(response.headers["cache-control"], "no-cache")
        self.assertRegex(etag, r'^"[0-9a-f]{32}"$')

        for header in (etag, f"W/{etag}", f'"other", {etag}', "*"):
            with self.subTest(if_none_match=header):
                not_modified = self.client.get(
                    LIST_URL, headers={"If-None-Match": header}
                )
                self.assertEqual(not_modified.status_code, 304)
                self.assertEqual(not_modified.content, b"")
                self.assertEqual(not_modified.headers["etag"], etag)

        self.assertEqual(
            self.client.get(LIST_URL, headers={"If-None-Match": '"stale"'}).status_code,
            200,
        )

        Appliance.objects.create(name="Kettle")
        changed = self.client.get(LIST_URL, headers={"If-None-Match": etag})
        self.assertEqual(changed.status_code, 200)
        self.assertNotEqual(changed.headers["etag"], etag)

    def test_etag_differs_per_filter(self):
        Appliance.objects.create(name="TV")
        self.assertNotEqual(
            self.client.get(LIST_URL + "?name=fan").headers["etag"],
            self.client.get(LIST_URL + "?name=tv").headers["etag"],
        )

    def test_cache_outage_still_serves_requests(self):
        with mock.patch.object(
            appliance_cache.cache, "get", side_effect=ConnectionError("redis down")
        ):
            response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"id": self.fan.id, "name": "Fan"}])
