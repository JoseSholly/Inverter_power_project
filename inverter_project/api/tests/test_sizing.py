from django.test import SimpleTestCase

from api.common import sizing


class SizingModelTests(SimpleTestCase):
    def test_battery_capacity_includes_inverter_losses_and_depth_of_discharge(self):
        # 3420 Wh / (24 V x 0.8 x 0.5) = 356.25 Ah
        self.assertEqual(sizing.battery_capacity_ah(3420, 24), 356.25)

    def test_battery_count_is_series_times_parallel(self):
        self.assertEqual(
            sizing.number_of_batteries(450, 200, 12), 3
        )  # 1 in series x 3 strings
        self.assertEqual(sizing.number_of_batteries(356.25, 200, 24), 4)  # 2 x 2
        self.assertEqual(sizing.number_of_batteries(390, 200, 48), 8)  # 4 x 2
        self.assertEqual(sizing.number_of_batteries(0, 200, 24), 0)

    def test_ceil_ignores_float_noise(self):
        # 0.1 + 0.2 = 0.30000000000000004; must not round up to an extra unit
        self.assertEqual(sizing.safe_ceil((0.1 + 0.2) * 10), 3)
        self.assertEqual(sizing.number_of_panels(1050.0000000001, 350), 3)

    def test_solar_array_and_currents(self):
        self.assertEqual(
            sizing.solar_array_capacity_wp(3420), 712.5
        )  # 3420 / (6 h x 0.8)
        self.assertEqual(sizing.number_of_panels(712.5, 350), 3)
        self.assertEqual(sizing.array_current_a(3, 350, 24), 43.75)
        self.assertEqual(sizing.controller_current_a(3, 350, 24), 54.69)

    def test_zero_guards(self):
        self.assertEqual(sizing.battery_capacity_ah(100, 0), 0)
        self.assertEqual(sizing.number_of_batteries(100, 0, 24), 0)
        self.assertEqual(sizing.number_of_panels(100, 0), 0)
        self.assertEqual(sizing.array_current_a(1, 300, 0), 0)
        self.assertEqual(sizing.controller_current_a(1, 300, 0), 0)
