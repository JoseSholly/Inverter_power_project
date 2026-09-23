from django.core.management.base import BaseCommand

from power_calculator.cache import invalidate


class Command(BaseCommand):
    help = (
        "Invalidate the cached appliance catalogue. Needed after bulk changes that skip model "
        "signals (QuerySet.update(), bulk_create(), raw SQL)."
    )

    def handle(self, *args, **options):
        invalidate()
        self.stdout.write(self.style.SUCCESS("Appliance cache invalidated."))
