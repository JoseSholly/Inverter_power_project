from django.test import SimpleTestCase

from api.v1.calculator import LoadItem as V1LoadItem
from api.v1.calculator import V1CalculationInput, V1Calculator
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
        # energy = 75x5 + 120x4 + 56x7 = 1247 Wh
        self.assertEqual(result.total_load, 251.0)
        self.assertEqual(result.inverter_rating, 0.31)
        self.assertEqual(result.total_battery_capacity, 129.9)
        self.assertEqual(result.numbers_of_batteries, 2)
        self.assertEqual(result.total_solar_panel_capacity_needed, 259.79)
        self.assertEqual(result.numbers_of_solar_panel, 1)
        self.assertEqual(result.total_current, 14.58)
        self.assertEqual(result.controller_current, 18.23)

    def test_energy_uses_each_items_backup_time(self):
        items = (LoadItem(2, 100.0, 3.0), LoadItem(1, 50.0, 10.0))
        self.assertEqual(V2Calculator.energy(items), 1100.0)
        self.assertEqual(V2Calculator.total_load(items), 250.0)


class V1V2ConsistencyTests(SimpleTestCase):
    """With the same backup time for every appliance, both versions must agree."""

    def test_same_inputs_give_same_results(self):
        loads = [(6, 10), (3, 75), (1, 120), (1, 150), (2, 150)]
        for voltage in (12, 24, 48):
            for backup_time in (1, 4, 9):
                with self.subTest(voltage=voltage, backup_time=backup_time):
                    v1 = V1Calculator().calculate(
                        V1CalculationInput(
                            backup_time=backup_time,
                            battery_capacity=200,
                            system_voltage=voltage,
                            solar_panel_watt=350,
                            items=tuple(V1LoadItem(q, p) for q, p in loads),
                        )
                    )
                    v2 = V2Calculator().calculate(
                        V2CalculationInput(
                            battery_capacity=200.0,
                            system_voltage=float(voltage),
                            solar_panel_watt=350.0,
                            items=tuple(LoadItem(q, float(p), float(backup_time)) for q, p in loads),
                        )
                    )
                    self.assertEqual(v1.__dict__, v2.__dict__)
