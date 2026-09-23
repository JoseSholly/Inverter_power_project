from django.test import SimpleTestCase

from api.v1.calculator import LoadItem, V1CalculationInput, V1Calculator


def make_input(**overrides) -> V1CalculationInput:
    data = {
        "backup_time": 4,
        "battery_capacity": 200,
        "system_voltage": 24,
        "solar_panel_watt": 350,
        "items": (LoadItem(6, 10), LoadItem(3, 75), LoadItem(1, 120), LoadItem(1, 150), LoadItem(2, 150)),
    }
    data.update(overrides)
    return V1CalculationInput(**data)


class V1CalculatorTests(SimpleTestCase):
    def test_readme_example(self):
        result = V1Calculator().calculate(make_input())
        self.assertEqual(result.total_load, 855)
        self.assertEqual(result.inverter_rating, 1.07)
        self.assertEqual(result.total_battery_capacity, 178.12)
        self.assertEqual(result.numbers_of_batteries, 2)
        self.assertEqual(result.total_solar_panel_capacity_needed, 712.5)
        self.assertEqual(result.numbers_of_solar_panel, 3)
        self.assertEqual(result.total_current, 43.75)

    def test_battery_count_is_series_times_parallel(self):
        calc = V1Calculator()
        # 12V: one battery per string, strings = ceil(needed / capacity)
        self.assertEqual(calc.number_of_batteries(450, 200, 12), 3)
        # 24V: 2 in series per string, 1 string
        self.assertEqual(calc.number_of_batteries(178.12, 200, 24), 2)
        # 24V needing more than one string used to return 2 regardless of load
        self.assertEqual(calc.number_of_batteries(500, 200, 24), 6)
        # 48V: 4 in series per string
        self.assertEqual(calc.number_of_batteries(390, 200, 48), 8)

    def test_large_load_on_48v_scales_battery_count(self):
        result = V1Calculator().calculate(make_input(system_voltage=48, items=(LoadItem(10, 1000),)))
        # 10 kW * 4 h / (48 V * 0.8) = 1041.67 Ah -> 6 strings of 4 batteries
        self.assertEqual(result.total_battery_capacity, 1041.67)
        self.assertEqual(result.numbers_of_batteries, 24)
