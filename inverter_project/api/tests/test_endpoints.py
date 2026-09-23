from django.test import TestCase
from django_bolt.testing import TestClient

from inverter_project.api import api
from power_calculator.models import Appliance

V1_URL = "/api/v1/power_calculator/calculate/"
V2_URL = "/api/v2/power_calculator/calculate/"


class EndpointTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.appliances = [Appliance.objects.create(name=name) for name in ("LED Light", "Radio", "Fridge")]

    def setUp(self):
        self.client = TestClient(api)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def v1_payload(self, **overrides):
        payload = {
            "backup_time": 4,
            "battery_capacity": 200,
            "system_voltage": 24,
            "solar_panel_watt": 350,
            "items": [{"id": self.appliances[0].id, "quantity": 6, "power_rating": 10}],
        }
        payload.update(overrides)
        return payload

    def v2_payload(self, **overrides):
        payload = {
            "system_voltage": 24.0,
            "battery_capacity": 200.0,
            "solar_panel_watt": 350.0,
            "items": [{"id": self.appliances[2].id, "quantity": 1, "power_rating": 120.0, "backup_time": 4.0}],
        }
        payload.update(overrides)
        return payload

    def test_appliance_lists(self):
        for version in ("v1", "v2"):
            response = self.client.get(f"/api/{version}/power_calculator/appliances/")
            self.assertEqual(response.status_code, 200)
            self.assertEqual({a["name"] for a in response.json()}, {"LED Light", "Radio", "Fridge"})
            self.assertEqual(set(response.json()[0]), {"id", "name"})

    def test_v1_calculate(self):
        response = self.client.post(V1_URL, json=self.v1_payload())
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total_load"], 60)
        self.assertEqual(body["numbers_of_batteries"], 2)
        self.assertEqual(body["items"], [{"id": self.appliances[0].id, "name": "LED Light", "quantity": 6, "power_rating": 10}])

    def test_v1_defaults_quantity_and_power_rating(self):
        response = self.client.post(V1_URL, json=self.v1_payload(items=[{"id": self.appliances[1].id}]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"][0]["quantity"], 1)

    def test_v2_calculate(self):
        response = self.client.post(V2_URL, json=self.v2_payload())
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total_load"], 120.0)
        self.assertEqual(body["total_battery_capacity"], 20.0)
        self.assertEqual(body["items"][0]["name"], "Fridge")

    def test_unknown_appliance_is_422(self):
        for url, payload in ((V1_URL, self.v1_payload(items=[{"id": 9999}])),
                             (V2_URL, self.v2_payload(items=[{"id": 9999, "quantity": 1, "power_rating": 1, "backup_time": 1}]))):
            response = self.client.post(url, json=payload)
            self.assertEqual(response.status_code, 422)
            self.assertIn("9999", response.json()["detail"][0]["msg"])

    def test_invalid_input_is_422(self):
        cases = [
            (V1_URL, self.v1_payload(battery_capacity=123)),
            (V1_URL, self.v1_payload(system_voltage=36)),
            (V1_URL, self.v1_payload(backup_time=0)),
            (V1_URL, self.v1_payload(items=[])),
            (V2_URL, self.v2_payload(system_voltage=0)),
            (V2_URL, self.v2_payload(items=[])),
        ]
        for url, payload in cases:
            with self.subTest(url=url, payload=payload):
                self.assertEqual(self.client.post(url, json=payload).status_code, 422)
