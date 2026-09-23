"""Upper bounds for request values, shared by every API version.

They keep inputs physically plausible for a home system, keep the maths far
away from integer/float overflow, and keep appliance IDs inside the database's
64-bit integer range (larger IDs used to crash the lookup with a 500).
"""

MAX_APPLIANCE_ID = 2**63 - 1
MAX_ITEMS = 100
MAX_QUANTITY = 1_000
MAX_POWER_RATING_W = 100_000
MAX_BACKUP_TIME_H = 24
"""The sizing model recharges the batteries from solar once per day."""
MAX_SYSTEM_VOLTAGE_V = 240
MAX_BATTERY_CAPACITY_AH = 5_000
MAX_SOLAR_PANEL_W = 1_000

MAX_NAME_FILTER_LENGTH = 100
"""Longest accepted `?name=` filter on the appliance endpoints."""
