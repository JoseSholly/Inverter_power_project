from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from power_calculator.appliance_catalog import DEFAULT_APPLIANCES
from power_calculator.models import Appliance


def run(*args) -> str:
    out = StringIO()
    call_command("populate_appliances", *args, stdout=out)
    return out.getvalue()


class PopulateAppliancesTests(TestCase):
    def test_adds_every_appliance_in_catalog_order(self):
        output = run()
        names = list(Appliance.objects.order_by("id").values_list("name", flat=True))
        self.assertEqual(names, list(DEFAULT_APPLIANCES))
        self.assertIn(f"{len(DEFAULT_APPLIANCES)} added, 0 already present", output)

    def test_ids_referenced_by_the_readme_stay_stable(self):
        run()
        first_id = Appliance.objects.order_by("id").first().id
        by_offset = {a.id - first_id + 1: a.name for a in Appliance.objects.all()}
        expected = {1: "Wifi Router", 2: "Phone Charger", 3: "Fridge", 4: "TV", 8: "LED Light", 9: "Fan",
                    11: "Laptop", 12: "Refrigerator", 15: "Washing Machine", 17: "Home Theater", 18: "Radio"}
        for offset, name in expected.items():
            self.assertEqual(by_offset[offset], name)

    def test_dry_run_writes_nothing(self):
        output = run("--dry-run")
        self.assertEqual(Appliance.objects.count(), 0)
        self.assertIn("[dry run] Would add: LED Light", output)
        self.assertIn(f"[dry run] {len(DEFAULT_APPLIANCES)} would be added, 0 already present", output)

    def test_is_idempotent(self):
        run()
        output = run()
        self.assertEqual(Appliance.objects.count(), len(DEFAULT_APPLIANCES))
        self.assertIn(f"0 added, {len(DEFAULT_APPLIANCES)} already present", output)

    def test_existing_names_match_case_and_whitespace_insensitively(self):
        Appliance.objects.create(name="  led   LIGHT ")
        Appliance.objects.create(name="My Custom Heater")
        output = run("--dry-run")
        self.assertNotIn("Would add: LED Light", output)
        self.assertIn(f"{len(DEFAULT_APPLIANCES) - 1} would be added, 1 already present", output)
        run()
        self.assertEqual(Appliance.objects.filter(name__iexact="led light").count(), 0)
        self.assertEqual(Appliance.objects.count(), len(DEFAULT_APPLIANCES) + 1)  # custom one kept

    def test_verbosity_2_lists_existing(self):
        run()
        self.assertIn("Already exists: Fridge", run("-v", "2"))

    def test_catalog_has_no_duplicates_or_blank_names(self):
        normalized = [" ".join(n.split()).casefold() for n in DEFAULT_APPLIANCES]
        self.assertEqual(len(normalized), len(set(normalized)))
        self.assertTrue(all(normalized))

    def test_invalid_catalog_aborts_without_writing(self):
        with mock.patch(
            "power_calculator.management.commands.populate_appliances.DEFAULT_APPLIANCES", ("Fan", "fan")
        ):
            with self.assertRaisesMessage(CommandError, "Duplicate appliance in catalog"):
                run()
        self.assertEqual(Appliance.objects.count(), 0)
