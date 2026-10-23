from django.test import SimpleTestCase, override_settings
from django_bolt import BoltAPI
from django_bolt.testing import TestClient

from api.common.rate_limit import limited


def make_app() -> BoltAPI:
    app = BoltAPI()

    @app.get("/ping")
    @limited
    async def ping() -> dict:
        return {"ok": True}

    return app


class RateLimitTests(SimpleTestCase):
    @override_settings(RATE_LIMIT_RPS=1, RATE_LIMIT_BURST=3)
    def test_requests_over_the_burst_get_429_with_retry_after(self):
        with TestClient(make_app()) as client:
            codes = [client.get("/ping").status_code for _ in range(10)]
            blocked = client.get("/ping")
        self.assertEqual(codes[:3], [200, 200, 200])
        self.assertIn(429, codes)
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(blocked.headers["retry-after"], "1")
        self.assertIn("Rate limit exceeded", blocked.json()["detail"])

    @override_settings(RATE_LIMIT_RPS=0)
    def test_zero_turns_the_limit_off(self):
        with TestClient(make_app()) as client:
            codes = {client.get("/ping").status_code for _ in range(50)}
        self.assertEqual(codes, {200})

    def test_real_endpoints_are_not_limited_under_the_test_runner(self):
        from django.conf import settings

        self.assertEqual(settings.RATE_LIMIT_RPS, 0)
