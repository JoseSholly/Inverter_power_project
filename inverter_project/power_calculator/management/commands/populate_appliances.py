from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from power_calculator.appliance_catalog import DEFAULT_APPLIANCES
from power_calculator.cache import invalidate
from power_calculator.models import Appliance


def _normalize(name: str) -> str:
    return " ".join(name.split()).casefold()


class Command(BaseCommand):
    help = (
        "Add the default appliances to the database. Existing appliances are left untouched "
        "(names are matched case-insensitively), so the command is safe to run repeatedly."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be added without writing to the database.",
        )

    def handle(self, *args, dry_run: bool = False, **options):
        verbosity = options.get("verbosity", 1)
        catalog = self._validated_catalog()

        existing = {_normalize(name) for name in Appliance.objects.values_list("name", flat=True)}
        to_create = [name for name in catalog if _normalize(name) not in existing]
        already_present = len(catalog) - len(to_create)

        if verbosity >= 2:
            for name in catalog:
                if name not in to_create:
                    self.stdout.write(self.style.WARNING(f"Already exists: {name}"))

        prefix = "[dry run] Would add" if dry_run else "Added"
        if verbosity >= 1:
            for name in to_create:
                self.stdout.write(self.style.SUCCESS(f"{prefix}: {name}"))

        if not dry_run and to_create:
            # One transaction so a failure never leaves a half-populated table,
            # and create in catalog order so IDs follow the catalog.
            with transaction.atomic():
                for name in to_create:
                    Appliance.objects.create(name=name)
            invalidate()  # signals already did this per row; one explicit bump for clarity

        summary = (
            f"{'[dry run] ' if dry_run else ''}"
            f"{len(to_create)} {'would be added' if dry_run else 'added'}, "
            f"{already_present} already present, {len(catalog)} in catalog."
        )
        self.stdout.write(self.style.NOTICE(summary) if dry_run else self.style.SUCCESS(summary))

    @staticmethod
    def _validated_catalog() -> list[str]:
        seen: set[str] = set()
        catalog = []
        for name in DEFAULT_APPLIANCES:
            clean = " ".join(name.split())
            if not clean:
                raise CommandError("The appliance catalog contains a blank name.")
            if len(clean) > Appliance._meta.get_field("name").max_length:
                raise CommandError(f"Appliance name is too long: {clean!r}")
            key = _normalize(clean)
            if key in seen:
                raise CommandError(f"Duplicate appliance in catalog: {clean!r}")
            seen.add(key)
            catalog.append(clean)
        return catalog
