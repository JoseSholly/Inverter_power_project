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

    def test_recommended_voltage_tiers_and_boundaries(self):
        cases = (
            (0.31, 12),
            (1.0, 12),
            (1.01, 24),
            (3.0, 24),
            (3.01, 48),
            (10.0, 48),
        )
        for kva, voltage in cases:
            with self.subTest(kva=kva):
                self.assertEqual(sizing.recommended_system_voltage(kva), voltage)

    def test_voltage_advice_low_voltage_warning(self):
        rec, warnings = sizing.voltage_advice(12, 2.5, 100, 200)
        self.assertEqual(rec, 24)
        (w,) = warnings
        self.assertEqual(w.code, sizing.LOW_VOLTAGE)
        self.assertEqual(w.recommended_system_voltage, 24)
        self.assertIn("24V is recommended", w.message)

    def test_voltage_advice_no_warning_at_or_above_recommendation(self):
        self.assertEqual(sizing.voltage_advice(24, 2.5, 100, 200)[1], [])
        self.assertEqual(sizing.voltage_advice(48, 2.5, 100, 200)[1], [])

    def test_many_strings_warns_even_when_voltage_is_high_enough(self):
        # 0.4 kVA -> 12V is enough, but 1000 Ah of 200 Ah batteries = 5 strings
        rec, warnings = sizing.voltage_advice(12, 0.4, 1000, 200)
        self.assertEqual(rec, 12)
        (w,) = warnings
        self.assertEqual(w.code, sizing.MANY_PARALLEL_STRINGS)
        self.assertEqual(w.recommended_system_voltage, 24)
        self.assertIn("5 parallel", w.message)

    def test_many_strings_at_top_voltage_has_no_voltage_suggestion(self):
        (w,) = sizing.voltage_advice(48, 0.4, 1000, 200)[1]
        self.assertIsNone(w.recommended_system_voltage)
        self.assertIn("larger batteries", w.message)

    def test_both_warnings_are_independent(self):
        _, warnings = sizing.voltage_advice(12, 2.5, 1000, 200)
        self.assertEqual(
            [w.code for w in warnings],
            [sizing.LOW_VOLTAGE, sizing.MANY_PARALLEL_STRINGS],
        )

    def test_custom_thresholds(self):
        tiers = ((0.5, 12), (1.0, 24))
        self.assertEqual(sizing.recommended_system_voltage(0.8, tiers), 24)
        _, warnings = sizing.voltage_advice(12, 0.1, 400, 200, max_parallel_strings=1)
        self.assertEqual(warnings[0].code, sizing.MANY_PARALLEL_STRINGS)

    def test_zero_guards(self):
        self.assertEqual(sizing.battery_capacity_ah(100, 0), 0)
        self.assertEqual(sizing.number_of_batteries(100, 0, 24), 0)
        self.assertEqual(sizing.number_of_panels(100, 0), 0)
        self.assertEqual(sizing.array_current_a(1, 300, 0), 0)
        self.assertEqual(sizing.controller_current_a(1, 300, 0), 0)
