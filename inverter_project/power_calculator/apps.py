from django.apps import AppConfig


class PowerCalculatorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "power_calculator"

    def ready(self):
        from . import (  # noqa: F401  (register signal receivers and system checks)
            checks,
            signals,
        )
