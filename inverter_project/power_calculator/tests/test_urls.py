from django.test import SimpleTestCase
from django.urls import reverse, resolve
from inverter_project.api.v1.views import AppliancesListView, CalculationsListView, CalculationCreateView, CalculationUpdateView, CalculationDeleteView
import uuid
class TestUrls(SimpleTestCase):
    def test_appliances_list(self):
        url = reverse("appliance-list")
        resolved_func = resolve(url).func

        # Check if the resolved function corresponds to AppliancesListView's as_view function
        self.assertEqual(resolved_func.view_class, AppliancesListView)

    def test_calculations_list(self):
        url = reverse("calculation-list")
        resolved_func = resolve(url).func

        # Check if the resolved function corresponds to CalculationsListView's as_view function
        self.assertEqual(resolved_func.view_class, CalculationsListView)

    def test_calculation_create(self):
        url: str = reverse('calculation-create')
        resolved_url = resolve(url).func

        # Check if the resolved function corresponds to CalculationCreateView's as_view function
        self.assertAlmostEqual(resolved_url.view_class, CalculationCreateView) 

    
    def test_calculation_update(self):
        # Create a sample UUID for testing
        sample_uuid = uuid.uuid4()

        # Reverse the URL to generate the correct path with the UUID
        url = reverse("calculation-update", kwargs={"pk": sample_uuid})

        # Resolve the URL and check if it maps to the correct view
        resolved_url = resolve(url).func

        # Check if the resolved function corresponds to CalculationCreateView's as_view function
        self.assertAlmostEqual(resolved_url.view_class, CalculationUpdateView) 

    def test_calculation_delete(self):
        # Create a sample UUID for testing
        sample_uuid = uuid.uuid4()

        # Reverse the URL to generate the correct path with the UUID
        url = reverse("calculation-delete", kwargs={"pk": sample_uuid})

        # Resolve the URL and check if it maps to the correct view
        resolved_url = resolve(url).func

        # Check if the resolved function corresponds to CalculationCreateView's as_view function
        self.assertAlmostEqual(resolved_url.view_class, CalculationDeleteView) 