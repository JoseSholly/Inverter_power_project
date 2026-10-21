import msgspec


class ApplianceOut(msgspec.Struct):
    id: int
    name: str


class WarningOut(msgspec.Struct):
    code: str  # stable, e.g. LOW_VOLTAGE or MANY_PARALLEL_STRINGS
    message: str  # human-readable, English
    recommended_system_voltage: int | None = None  # suggested fix, if there is one
