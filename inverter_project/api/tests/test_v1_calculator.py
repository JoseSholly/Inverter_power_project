from django.test import SimpleTestCase

from api.v1.calculator import LoadItem, V1CalculationInput, V1Calculator


def make_input(**overrides) -> V1CalculationInput:
    data = {
        "backup_time": 4,
        "battery_capacity": 200,
        "system_voltage": 24,
        "solar_panel_watt": 350,
        "items": (
            LoadItem(6, 10),
            LoadItem(3, 75),
            LoadItem(1, 120),
            LoadItem(1, 150),
            LoadItem(2, 150),
        ),
    }
    data.update(overrides)
    return V1CalculationInput(**data)


class V1CalculatorTests(SimpleTestCase):
    def test_readme_example(self):
        result = V1Calculator().calculate(make_input())
        self.assertEqual(result.total_load, 855)
        self.assertEqual(result.inverter_rating, 1.07)
        self.assertEqual(result.total_battery_capacity, 356.25)
        self.assertEqual(result.numbers_of_batteries, 4)
        self.assertEqual(result.total_solar_panel_capacity_needed, 712.5)
        self.assertEqual(result.numbers_of_solar_panel, 3)
        self.assertEqual(result.total_current, 43.75)
        self.assertEqual(result.controller_current, 54.69)

    def test_energy_uses_one_backup_time(self):
        self.assertEqual(V1Calculator.energy(855, 4), 3420)

    def test_large_load_on_48v_scales_battery_count(self):
        result = V1Calculator().calculate(
            make_input(system_voltage=48, items=(LoadItem(10, 1000),))
        )
        # 40 kWh / (48 V x 0.8 x 0.5) = 2083.33 Ah -> 11 strings of 4 batteries
        self.assertEqual(result.total_battery_capacity, 2083.33)
        self.assertEqual(result.numbers_of_batteries, 44)
