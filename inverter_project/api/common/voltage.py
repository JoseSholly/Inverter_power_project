"""System-voltage advice with the thresholds taken from Django settings."""

from django.conf import settings

from . import sizing


def advise(
    system_voltage: float,
    inverter_kva: float,
    bank_capacity_ah: float,
    battery_capacity_ah: float,
) -> tuple[int, tuple[sizing.SizingWarning, ...]]:
    recommended, warnings = sizing.voltage_advice(
        system_voltage,
        inverter_kva,
        bank_capacity_ah,
        battery_capacity_ah,
        tiers=(
            (settings.VOLTAGE_12V_MAX_KVA, 12),
            (settings.VOLTAGE_24V_MAX_KVA, 24),
        ),
        max_parallel_strings=settings.MAX_PARALLEL_STRINGS,
    )
    return recommended, tuple(warnings)
