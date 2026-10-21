"""Realistic end-to-end cases through both calculate endpoints.

Appliances come from the real catalog (`populate_appliances`), so these also
guard the names the frontend sends. Expected values were produced by the
endpoints and checked by hand against the sizing formulas in the README.
"""

from django.core.management import call_command
from django.test import TestCase
from django_bolt.testing import TestClient

from inverter_project.api import api
from power_calculator.models import Appliance

V1_URL = "/api/v1/power_calculator/calculate/"
V2_URL = "/api/v2/power_calculator/calculate/"

LOW = "LOW_VOLTAGE"
MANY = "MANY_PARALLEL_STRINGS"

# Each case: system voltage, battery Ah, panel W, then (appliance, qty, W, hours).
# v1 uses one backup time for everything (v1_hours) instead of one per appliance.
CASES = {
    "1 small flat": {
        "volts": 12,
        "ah": 200,
        "panel": 350,
        "v1_hours": 6,
        "items": [
            ("LED Light", 5, 10, 6),
            ("Wifi Router", 1, 12, 12),
            ("Phone Charger", 3, 10, 3),
            ("TV", 1, 80, 4),
        ],
    },
    "2 family home": {
        "volts": 24,
        "ah": 200,
        "panel": 400,
        "v1_hours": 6,
        "items": [
            ("LED Light", 8, 10, 6),
            ("Ceiling Fan", 3, 70, 8),
            ("TV", 1, 120, 5),
            ("Refrigerator", 1, 150, 10),
            ("Laptop", 2, 65, 4),
        ],
    },
    "3 heavy kitchen on 12V": {
        "volts": 12,
        "ah": 200,
        "panel": 400,
        "v1_hours": 3,
        "items": [
            ("Refrigerator", 1, 200, 10),
            ("Microwave Oven", 1, 1000, 1),
            ("Electric Kettle", 1, 1500, 1),
            ("LED Light", 6, 10, 5),
        ],
    },
    "4 low power for 24h": {
        "volts": 24,
        "ah": 100,
        "panel": 400,
        "v1_hours": 24,
        "items": [
            ("Security Cameras", 4, 15, 24),
            ("Wifi Router", 1, 12, 24),
            ("Chest Freezer", 1, 200, 24),
        ],
    },
    "5 workshop on 12V": {
        "volts": 12,
        "ah": 100,
        "panel": 400,
        "v1_hours": 8,
        "items": [
            ("Water Pump", 1, 750, 3),
            ("Desktop Computer", 2, 200, 8),
            ("Chest Freezer", 1, 200, 24),
            ("LED Light", 10, 10, 8),
        ],
    },
    "6 large home on 48V": {
        "volts": 48,
        "ah": 250,
        "panel": 450,
        "v1_hours": 6,
        "items": [
            ("Air Conditioner (AC)", 1, 1500, 4),
            ("Fridge", 1, 150, 10),
            ("LED Light", 12, 10, 6),
            ("TV", 2, 120, 5),
            ("Washing Machine", 1, 500, 1),
        ],
    },
    "7 huge load on 48V": {
        "volts": 48,
        "ah": 100,
        "panel": 400,
        "v1_hours": 8,
        "items": [
            ("Air Conditioner (AC)", 2, 1500, 8),
            ("Chest Freezer", 1, 200, 24),
            ("Electric Cooker", 1, 2000, 2),
        ],
    },
    "8 exactly 800W (1.00 kVA)": {
        "volts": 12,
        "ah": 250,
        "panel": 400,
        "v1_hours": 4,
        "items": [("LED Light", 10, 10, 4), ("Refrigerator", 1, 700, 4)],
    },
    "9 840W (1.05 kVA)": {
        "volts": 12,
        "ah": 250,
        "panel": 400,
        "v1_hours": 4,
        "items": [("LED Light", 10, 10, 4), ("Refrigerator", 1, 740, 4)],
    },
}

# (total_load, inverter_kva, bank_ah, batteries, panels, controller_a,
#  recommended_voltage, [(warning code, suggested voltage)])
EXPECTED_V2 = {
    "1 small flat": (172, 0.21, 177.92, 1, 1, 36.46, 12, []),
    "2 family home": (690, 0.86, 497.92, 6, 3, 62.5, 12, []),
    "3 heavy kitchen on 12V": (
        2760,
        3.45,
        1000.0,
        5,
        3,
        125.0,
        48,
        [(LOW, 48), (MANY, 24)],
    ),
    "4 low power for 24h": (272, 0.34, 680.0, 14, 4, 83.33, 12, [(MANY, 48)]),
    "5 workshop on 12V": (
        1450,
        1.81,
        2302.08,
        24,
        6,
        250.0,
        24,
        [(LOW, 24), (MANY, 24)],
    ),
    "6 large home on 48V": (2510, 3.14, 516.67, 12, 5, 58.59, 48, []),
    "7 huge load on 48V": (5200, 6.5, 1708.33, 72, 18, 187.5, 48, [(MANY, None)]),
    "8 exactly 800W (1.00 kVA)": (800, 1.0, 666.67, 3, 2, 83.33, 12, []),
    "9 840W (1.05 kVA)": (840, 1.05, 700.0, 3, 2, 83.33, 24, [(LOW, 24)]),
}

EXPECTED_V1 = {
    "1 small flat": (172, 0.21, 215.0, 2, 1, 36.46, 12, []),
    "2 family home": (690, 0.86, 431.25, 6, 3, 62.5, 12, []),
    "3 heavy kitchen on 12V": (
        2760,
        3.45,
        1725.0,
        9,
        5,
        208.33,
        48,
        [(LOW, 48), (MANY, 24)],
    ),
    "4 low power for 24h": (272, 0.34, 680.0, 14, 4, 83.33, 12, [(MANY, 48)]),
    "5 workshop on 12V": (
        1450,
        1.81,
        2416.67,
        25,
        7,
        291.67,
        24,
        [(LOW, 24), (MANY, 24)],
    ),
    # Flat 6 h for everything needs 4 strings, so v1 warns where v2 does not.
    "6 large home on 48V": (2510, 3.14, 784.37, 16, 7, 82.03, 48, [(MANY, None)]),
    "7 huge load on 48V": (5200, 6.5, 2166.67, 88, 22, 229.17, 48, [(MANY, None)]),
    "8 exactly 800W (1.00 kVA)": (800, 1.0, 666.67, 3, 2, 83.33, 12, []),
    "9 840W (1.05 kVA)": (840, 1.05, 700.0, 3, 2, 83.33, 24, [(LOW, 24)]),
}


class SampleCaseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("populate_appliances", verbosity=0)
        cls.ids = {a.name: a.id for a in Appliance.objects.all()}

    def setUp(self):
        self.client = TestClient(api)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def v1_payload(self, case, **overrides):
        payload = {
            "backup_time": case["v1_hours"],
            "battery_capacity": case["ah"],
            "system_voltage": case["volts"],
            "solar_panel_watt": case["panel"],
            "items": [
                {"id": self.ids[name], "quantity": qty, "power_rating": watts}
                for name, qty, watts, _ in case["items"]
            ],
        }
        return payload | overrides

    def v2_payload(self, case):
        return {
            "system_voltage": case["volts"],
            "battery_capacity": case["ah"],
            "solar_panel_watt": case["panel"],
            "items": [
                {
                    "id": self.ids[name],
                    "quantity": qty,
                    "power_rating": watts,
                    "backup_time": hours,
                }
                for name, qty, watts, hours in case["items"]
            ],
        }

    def assert_matches(self, body, expected):
        load, kva, ah, batteries, panels, controller, recommended, warnings = expected
        self.assertEqual(body["total_load"], load)
        self.assertEqual(body["inverter_rating"], kva)
        self.assertEqual(body["total_battery_capacity"], ah)
        self.assertEqual(body["numbers_of_batteries"], batteries)
        self.assertEqual(body["numbers_of_solar_panel"], panels)
        self.assertEqual(body["controller_current"], controller)
        self.assertEqual(body["recommended_system_voltage"], recommended)
        self.assertEqual(
            [(w["code"], w["recommended_system_voltage"]) for w in body["warnings"]],
            warnings,
        )
        for warning in body["warnings"]:
            self.assertTrue(warning["message"])

    def test_v2_cases(self):
        for name, case in CASES.items():
            with self.subTest(case=name):
                response = self.client.post(V2_URL, json=self.v2_payload(case))
                self.assertEqual(response.status_code, 200, response.json())
                body = response.json()
                self.assert_matches(body, EXPECTED_V2[name])
                self.assertEqual(
                    [item["name"] for item in body["items"]],
                    [item[0] for item in case["items"]],
                )

    def test_v1_cases(self):
        for name, case in CASES.items():
            with self.subTest(case=name):
                response = self.client.post(V1_URL, json=self.v1_payload(case))
                self.assertEqual(response.status_code, 200, response.json())
                body = response.json()
                self.assert_matches(body, EXPECTED_V1[name])
                self.assertEqual(
                    [item["name"] for item in body["items"]],
                    [item[0] for item in case["items"]],
                )

    def test_v1_accepts_small_and_large_real_world_sizes(self):
        case = CASES["2 family home"]
        for battery, panel in ((65, 100), (75, 250), (120, 500), (250, 650)):
            with self.subTest(battery=battery, panel=panel):
                response = self.client.post(
                    V1_URL,
                    json=self.v1_payload(
                        case, battery_capacity=battery, solar_panel_watt=panel
                    ),
                )
                self.assertEqual(response.status_code, 200, response.json())

    def test_v1_rejects_battery_sizes_it_does_not_offer(self):
        case = CASES["4 low power for 24h"]
        response = self.client.post(
            V1_URL, json=self.v1_payload(case, battery_capacity=90)
        )
        self.assertEqual(response.status_code, 422)

    def test_v1_rejects_non_standard_voltage_and_v2_non_multiples_of_12(self):
        case = CASES["2 family home"]
        v1 = self.client.post(V1_URL, json=self.v1_payload(case, system_voltage=36))
        v2 = self.client.post(
            V2_URL, json=self.v2_payload(case) | {"system_voltage": 30}
        )
        self.assertEqual((v1.status_code, v2.status_code), (422, 422))
