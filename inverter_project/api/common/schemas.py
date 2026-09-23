import msgspec


class ApplianceOut(msgspec.Struct):
    id: int
    name: str
