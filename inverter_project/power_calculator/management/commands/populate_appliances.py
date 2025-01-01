from django.core.management.base import BaseCommand
from power_calculator.models import Appliance


class Command(BaseCommand):
    help = "Populates the database with predefined appliances"

    def handle(self, *args, **kwargs):
        appliances = [
            "Wifi Router",
            "Phone Charger",
            "Fridge",
            "TV",
            "Microwave Oven",
            "Tungsten Bulb",
            "Tube Light",
            "LED Light",
            "Fan",
            "Desktop Computer",
            "Laptop",
            "Refrigerator",
            "Air Conditioner (AC)",
            "Toaster",
            "Washing Machine",
            "Gaming Console",
            "Home Theater",
            "Radio",
            "Wifi-Router",
            "Electric Blender",
            "Electric Kettle",
            "Printer",
            "Phone",
            "Security Cameras",
            "Electric shaver",
        ]

        for appliance_name in appliances:
            appliance, created = Appliance.objects.get_or_create(name=appliance_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Added: {appliance_name}"))
            else:
                self.stdout.write(
                    self.style.WARNING(f"Already exists: {appliance_name}")
                )
