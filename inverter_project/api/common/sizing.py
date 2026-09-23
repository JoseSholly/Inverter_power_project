"""Sizing model shared by every API version.

Each version decides how the energy demand is built (one backup time vs a
backup time per appliance); from energy onward all versions use these
formulas, so their results stay consistent. Pure Python, no Django imports.
"""

from math import ceil

POWER_FACTOR = 0.8
"""Typical household load power factor (W -> VA)."""

INVERTER_EFFICIENCY = 0.8
"""Conservative inverter + wiring efficiency (battery -> AC load)."""

BATTERY_DEPTH_OF_DISCHARGE = 0.5
"""Usable fraction of a lead-acid/tubular battery's rated capacity."""

BATTERY_UNIT_VOLTAGE = 12
"""Batteries are 12V units wired in series strings to reach the system voltage."""

PEAK_SUN_HOURS = 6
"""Average daily peak sun hours."""

SOLAR_SYSTEM_EFFICIENCY = 0.8
"""Panel derating, charge controller and battery charging losses."""

CONTROLLER_SAFETY_FACTOR = 1.25
"""Headroom for the charge controller over the array's nominal current."""


def safe_ceil(value: float) -> int:
    """ceil() that ignores float noise, e.g. 2.0000000000000004 -> 2."""
    return ceil(round(value, 9))


def inverter_rating_kva(total_load_w: float) -> float:
    return round(total_load_w / POWER_FACTOR / 1000, 2)


def battery_capacity_ah(energy_wh: float, system_voltage: float) -> float:
    """Battery bank capacity (Ah at the system voltage) that delivers energy_wh
    through the inverter without discharging below the allowed depth."""
    if system_voltage <= 0:
        return 0.0
    return round(
        energy_wh / (system_voltage * INVERTER_EFFICIENCY * BATTERY_DEPTH_OF_DISCHARGE),
        2,
    )


def number_of_batteries(
    bank_capacity_ah: float, battery_capacity_ah: float, system_voltage: float
) -> int:
    """12V batteries needed: batteries in series per string x parallel strings."""
    if battery_capacity_ah <= 0 or system_voltage <= 0 or bank_capacity_ah <= 0:
        return 0
    batteries_per_string = safe_ceil(system_voltage / BATTERY_UNIT_VOLTAGE)
    strings = safe_ceil(bank_capacity_ah / battery_capacity_ah)
    return batteries_per_string * strings


def solar_array_capacity_wp(energy_wh: float) -> float:
    """Array size (Wp) that replaces energy_wh each day after system losses."""
    return round(energy_wh / (PEAK_SUN_HOURS * SOLAR_SYSTEM_EFFICIENCY), 2)


def number_of_panels(array_capacity_wp: float, panel_watt: float) -> int:
    if panel_watt <= 0:
        return 0
    return safe_ceil(array_capacity_wp / panel_watt)


def array_current_a(panels: int, panel_watt: float, system_voltage: float) -> float:
    """Nominal current of the installed array at the system voltage."""
    if system_voltage <= 0:
        return 0.0
    return round(panels * panel_watt / system_voltage, 2)


def controller_current_a(
    panels: int, panel_watt: float, system_voltage: float
) -> float:
    """Charge controller rating for the installed array, with safety headroom."""
    if system_voltage <= 0:
        return 0.0
    return round(panels * panel_watt * CONTROLLER_SAFETY_FACTOR / system_voltage, 2)
