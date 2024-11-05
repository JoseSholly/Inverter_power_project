from django.test import SimpleTestCase
from django.urls import reverse, resolve
from api.views import AppliancesListView

class TestUrls(SimpleTestCase):
    def test_appliances_list(self):
        url = reverse("appliance-list")
        resolved_func = resolve(url).func

        # Check if the resolved function corresponds to AppliancesListView's as_view function
        self.assertEqual(resolved_func.view_class, AppliancesListView)
