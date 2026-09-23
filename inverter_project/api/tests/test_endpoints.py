from unittest import mock

from django.test import TestCase
from django_bolt.openapi.schema_generator import SchemaGenerator
from django_bolt.testing import TestClient

from inverter_project.api import api
from power_calculator.models import Appliance

V1_URL = "/api/v1/power_calculator/calculate/"
V2_URL = "/api/v2/power_calculator/calculate/"


class EndpointTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.appliances = [
            Appliance.objects.create(name=name)
            for name in ("LED Light", "Radio", "Fridge")
        ]

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
            "items": [
                {
                    "id": self.appliances[2].id,
                    "quantity": 1,
                    "power_rating": 120.0,
                    "backup_time": 4.0,
                }
            ],
        }
        payload.update(overrides)
        return payload

    def test_appliance_lists(self):
        for version in ("v1", "v2"):
            response = self.client.get(f"/api/{version}/power_calculator/appliances/")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                {a["name"] for a in response.json()}, {"LED Light", "Radio", "Fridge"}
            )
            self.assertEqual(set(response.json()[0]), {"id", "name"})

    def test_v1_calculate(self):
        response = self.client.post(V1_URL, json=self.v1_payload())
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total_load"], 60)
        self.assertEqual(body["total_battery_capacity"], 25.0)
        self.assertEqual(body["numbers_of_batteries"], 2)
        self.assertIn("controller_current", body)
        self.assertEqual(
            body["items"],
            [
                {
                    "id": self.appliances[0].id,
                    "name": "LED Light",
                    "quantity": 6,
                    "power_rating": 10,
                }
            ],
        )

    def test_v1_defaults_quantity_and_power_rating(self):
        response = self.client.post(
            V1_URL, json=self.v1_payload(items=[{"id": self.appliances[1].id}])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"][0]["quantity"], 1)

    def test_v2_calculate(self):
        response = self.client.post(V2_URL, json=self.v2_payload())
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total_load"], 120.0)
        self.assertEqual(body["total_battery_capacity"], 50.0)
        self.assertIn("total_current", body)
        self.assertEqual(body["items"][0]["name"], "Fridge")

    def test_unknown_appliance_is_422_pointing_at_the_item(self):
        known = self.appliances[0].id
        cases = (
            (V1_URL, self.v1_payload(items=[{"id": known}, {"id": 9999}])),
            (
                V2_URL,
                self.v2_payload(
                    items=[
                        {
                            "id": known,
                            "quantity": 1,
                            "power_rating": 1,
                            "backup_time": 1,
                        },
                        {
                            "id": 9999,
                            "quantity": 1,
                            "power_rating": 1,
                            "backup_time": 1,
                        },
                    ]
                ),
            ),
        )
        for url, payload in cases:
            with self.subTest(url=url):
                response = self.client.post(url, json=payload)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(
                    response.json()["detail"],
                    [
                        {
                            "type": "unknown_appliance",
                            "loc": ["body", "items", "1", "id"],
                            "msg": "Appliance with ID 9999 does not exist.",
                            "input": 9999,
                        }
                    ],
                )

    def test_malformed_requests_are_422(self):
        for body in (b'{"backup_time":', b"", b"[]", b"backup_time=4"):
            with self.subTest(body=body):
                response = self.client.post(
                    V1_URL, content=body, headers={"content-type": "application/json"}
                )
                self.assertEqual(response.status_code, 422)
                self.assertIn("detail", response.json())

    def test_out_of_range_values_are_422_not_500(self):
        v1_item = {"id": self.appliances[0].id, "quantity": 1, "power_rating": 10}
        v2_item = {
            "id": self.appliances[0].id,
            "quantity": 1,
            "power_rating": 10.0,
            "backup_time": 1.0,
        }
        cases = [
            (V1_URL, self.v1_payload(items=[{**v1_item, "id": 10**20}])),
            (V1_URL, self.v1_payload(items=[{**v1_item, "quantity": 2**63 - 1}])),
            (V1_URL, self.v1_payload(items=[{**v1_item, "power_rating": 2**63 - 1}])),
            (V1_URL, self.v1_payload(backup_time=25)),
            (V1_URL, self.v1_payload(items=[v1_item] * 101)),
            (V2_URL, self.v2_payload(items=[{**v2_item, "power_rating": 1e308}])),
            (V2_URL, self.v2_payload(items=[{**v2_item, "backup_time": 24.5}])),
            (V2_URL, self.v2_payload(system_voltage=252)),
            (V2_URL, self.v2_payload(battery_capacity=1e9)),
            (V2_URL, self.v2_payload(solar_panel_watt=5000)),
        ]
        for url, payload in cases:
            with self.subTest(url=url, payload=payload):
                self.assertEqual(self.client.post(url, json=payload).status_code, 422)

    def test_maximum_valid_request_succeeds(self):
        item = {
            "id": self.appliances[0].id,
            "quantity": 1000,
            "power_rating": 100000,
            "backup_time": 24,
        }
        response = self.client.post(
            V2_URL, json=self.v2_payload(system_voltage=240, items=[item] * 100)
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_input_is_422(self):
        cases = [
            (V1_URL, self.v1_payload(battery_capacity=123)),
            (V1_URL, self.v1_payload(system_voltage=36)),
            (V1_URL, self.v1_payload(backup_time=0)),
            (V1_URL, self.v1_payload(items=[])),
            (V2_URL, self.v2_payload(system_voltage=0)),
            (V2_URL, self.v2_payload(system_voltage=30)),
            (V2_URL, self.v2_payload(items=[])),
        ]
        for url, payload in cases:
            with self.subTest(url=url, payload=payload):
                self.assertEqual(self.client.post(url, json=payload).status_code, 422)

    def test_unexpected_error_is_generic_500_and_logged_with_traceback(self):
        with (
            mock.patch(
                "api.v1.routes.calculation_service.calculate",
                side_effect=RuntimeError("db down"),
            ),
            self.assertLogs("django.server", level="ERROR") as logs,
        ):
            response = self.client.post(V1_URL, json=self.v1_payload())
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "Internal Server Error"})
        self.assertNotIn("db down", response.text)
        self.assertIn("Unhandled exception", logs.output[0])
        self.assertIn("Traceback", logs.output[0])

    def test_paths_work_with_and_without_trailing_slash(self):
        for url in (V1_URL, V1_URL.rstrip("/")):
            with self.subTest(url=url):
                self.assertEqual(
                    self.client.post(url, json=self.v1_payload()).status_code, 200
                )
        for url in (V2_URL, V2_URL.rstrip("/")):
            with self.subTest(url=url):
                self.assertEqual(
                    self.client.post(url, json=self.v2_payload()).status_code, 200
                )
        for version in ("v1", "v2"):
            response = self.client.get(f"/api/{version}/power_calculator/appliances")
            self.assertEqual(response.status_code, 200)

    def test_wrong_method_is_405_with_allow_header(self):
        cases = []
        for version in ("v1", "v2"):
            calculate = f"/api/{version}/power_calculator/calculate/"
            appliances = f"/api/{version}/power_calculator/appliances/"
            for url in (calculate, calculate.rstrip("/")):
                cases += [
                    (method, url, "OPTIONS, POST")
                    for method in ("GET", "HEAD", "PUT", "PATCH", "DELETE")
                ]
            for url in (appliances, appliances.rstrip("/")):
                cases += [
                    (method, url, "GET, HEAD, OPTIONS")
                    for method in ("POST", "PUT", "PATCH", "DELETE")
                ]
        for method, url, allow in cases:
            with self.subTest(method=method, url=url):
                response = self.client.request(method, url)
                self.assertEqual(response.status_code, 405)
                self.assertEqual(response.headers["allow"], allow)
                if method != "HEAD":
                    self.assertEqual(
                        response.json(),
                        {"detail": f"Method not allowed. Allowed methods: {allow}."},
                    )

    def test_head_on_appliances(self):
        response = self.client.head("/api/v1/power_calculator/appliances/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")

    def test_unknown_path_is_still_404(self):
        self.assertEqual(
            self.client.get("/api/v1/power_calculator/nope/").status_code, 404
        )

    def test_docs_list_only_canonical_paths(self):
        # runbolt serves this schema at /api/docs/openapi.json; generate it the same way.
        paths = (
            SchemaGenerator(api, api._openapi_config).generate().to_schema()["paths"]
        )
        self.assertEqual(
            {path: sorted(methods) for path, methods in paths.items()},
            {
                "/api/v1/power_calculator/appliances/": ["get"],
                "/api/v1/power_calculator/calculate/": ["post"],
                "/api/v2/power_calculator/appliances/": ["get"],
                "/api/v2/power_calculator/calculate/": ["post"],
            },
        )
