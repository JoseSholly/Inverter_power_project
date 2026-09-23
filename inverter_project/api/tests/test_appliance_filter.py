from django.test import TestCase
from django_bolt.testing import TestClient

from inverter_project.api import api
from power_calculator.models import Appliance

NAMES = ("Fan", "Ceiling Fan", "Standing Fan", "TV", "CCTV Recorder", "Élan Heater")


class ApplianceNameFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for name in NAMES:
            Appliance.objects.create(name=name)

    def setUp(self):
        self.client = TestClient(api)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def names(self, query: str, version: str = "v1", slash: str = "/") -> list[str]:
        response = self.client.get(
            f"/api/{version}/power_calculator/appliances{slash}{query}"
        )
        self.assertEqual(response.status_code, 200, response.text)
        return [a["name"] for a in response.json()]

    def test_substring_case_insensitive_on_both_versions_and_paths(self):
        expected = ["Ceiling Fan", "Fan", "Standing Fan"]  # alphabetical
        for version in ("v1", "v2"):
            for slash in ("/", ""):
                for query in ("?name=fan", "?name=FAN", "?name=%20%20fAn%20"):
                    with self.subTest(version=version, slash=slash, query=query):
                        self.assertEqual(self.names(query, version, slash), expected)

    def test_matches_anywhere_in_the_name(self):
        self.assertEqual(self.names("?name=tv"), ["CCTV Recorder", "TV"])

    def test_non_ascii_case_folding(self):
        self.assertEqual(self.names("?name=%C3%A9LAN"), ["Élan Heater"])  # "éLAN"

    def test_no_match_returns_empty_list(self):
        self.assertEqual(self.names("?name=microwave"), [])

    def test_blank_or_missing_filter_returns_everything(self):
        for query in ("", "?name=", "?name=%20%20"):
            with self.subTest(query=query):
                self.assertEqual(len(self.names(query)), len(NAMES))

    def test_too_long_filter_is_422(self):
        response = self.client.get(
            "/api/v2/power_calculator/appliances/?name=" + "a" * 101
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"][0]["loc"], ["query", "name"])
        self.assertEqual(
            self.client.get(
                "/api/v2/power_calculator/appliances/?name=" + "a" * 100
            ).status_code,
            200,
        )
