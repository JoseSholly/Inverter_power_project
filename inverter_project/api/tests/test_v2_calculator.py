from django.test import SimpleTestCase

from api.v2.calculator import LoadItem, V2CalculationInput, V2Calculator


def make_input(**overrides) -> V2CalculationInput:
    data = {
        "system_voltage": 24.0,
        "battery_capacity": 200.0,
        "solar_panel_watt": 350.0,
        "items": (LoadItem(1, 75.0, 5.0), LoadItem(1, 120.0, 4.0), LoadItem(8, 7.0, 7.0)),
    }
    data.update(overrides)
    return V2CalculationInput(**data)


class V2CalculatorTests(SimpleTestCase):
    def test_readme_example(self):
        result = V2Calculator().calculate(make_input())
        self.assertEqual(result.total_load, 251.0)
        self.assertEqual(result.inverter_rating, 0.31)
        self.assertEqual(result.total_battery_capacity, 51.96)
        self.assertEqual(result.numbers_of_batteries, 2)
        self.assertEqual(result.total_solar_panel_capacity_needed, 259.79)
        self.assertEqual(result.numbers_of_solar_panel, 1)
        self.assertEqual(result.controller_current, 13.53)

    def test_per_item_backup_time_drives_energy(self):
        calc = V2Calculator()
        items = (LoadItem(2, 100.0, 3.0), LoadItem(1, 50.0, 10.0))
        self.assertEqual(calc.total_energy(items), 1100.0)
        self.assertEqual(calc.total_load(items), 250.0)

    def test_battery_count_is_series_times_parallel(self):
        calc = V2Calculator()
        self.assertEqual(calc.number_of_batteries(450, 200, 12), 3)
        self.assertEqual(calc.number_of_batteries(51.96, 200, 24), 2)
        self.assertEqual(calc.number_of_batteries(500, 200, 48), 12)

    def test_zero_guards(self):
        calc = V2Calculator()
        self.assertEqual(calc.number_of_batteries(100, 0, 24), 0)
        self.assertEqual(calc.number_of_panels(100, 0), 0)
        self.assertEqual(calc.total_battery_capacity(100, 0), 0)
        self.assertEqual(calc.controller_current(100, 0), 0)
