class UnknownApplianceError(Exception):
    """Raised when a calculation references appliance IDs that are not in the database."""

    def __init__(self, missing_ids: list[int]):
        self.missing_ids = sorted(set(missing_ids))
        ids = ", ".join(str(i) for i in self.missing_ids)
        super().__init__(f"Appliance(s) with ID {ids} do not exist in the database.")
