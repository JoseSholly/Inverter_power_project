from django.test import TestCase

from api.common.exceptions import UnknownApplianceError
from api.v1.services import V1CalculationRequest, V1CalculationService, V1ItemRequest
from api.v2.services import V2CalculationRequest, V2CalculationService, V2ItemRequest
from power_calculator.models import Appliance


class V1CalculationServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tv = Appliance.objects.create(name="TV")
        cls.fan = Appliance.objects.create(name="Fan")

    def request(self, *items):
        return V1CalculationRequest(
            backup_time=4, battery_capacity=200, system_voltage=12, solar_panel_watt=300, items=items
        )

    def test_resolves_names_in_request_order_with_one_query(self):
        request = self.request(V1ItemRequest(self.fan.id, 2, 75), V1ItemRequest(self.tv.id, 1, 120))
        with self.assertNumQueries(1):
            result = V1CalculationService().calculate(request)
        self.assertEqual([i.name for i in result.items], ["Fan", "TV"])
        self.assertEqual(result.output.total_load, 270)

    def test_unknown_appliance_raises(self):
        with self.assertRaises(UnknownApplianceError) as ctx:
            V1CalculationService().calculate(self.request(V1ItemRequest(9999, 1, 10)))
        self.assertEqual(ctx.exception.missing_ids, [9999])


class V2CalculationServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.fridge = Appliance.objects.create(name="Fridge")

    def request(self, *items):
        return V2CalculationRequest(system_voltage=24.0, battery_capacity=200.0, solar_panel_watt=350.0, items=items)

    def test_calculates_and_resolves_names(self):
        result = V2CalculationService().calculate(self.request(V2ItemRequest(self.fridge.id, 1, 150.0, 8.0)))
        self.assertEqual(result.items[0].name, "Fridge")
        self.assertEqual(result.output.total_load, 150.0)
        self.assertEqual(result.output.total_battery_capacity, 50.0)

    def test_unknown_appliance_raises(self):
        with self.assertRaises(UnknownApplianceError):
            V2CalculationService().calculate(self.request(V2ItemRequest(4242, 1, 10.0, 1.0)))
