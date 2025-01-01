from django.db import models
from .validators import validate_battery_capacity, validate_power_rating, validate_backup_time
import uuid
from .utils import SystemCalculationUtility


# Define the voltage choices
BATTERY_VOLTAGE_CHOICES = [
        (12, '12V'),
        (24, '24V'),
        (48, '48V'),
    ]

BATTERY_CAPACITY_CHOICES = [
        (150, '150Ah 12V'),
        (200, '200Ah 12V'),
        (220, '220Ah 12V'),
        (250, '250Ah 12V'),
    ]

SOLAR_PANEL_WATT= [
    (300, '300W'),
    (350, '350W'),
    (400, '400W'),
    (450, '450W'),
]

class Appliance(models.Model):
    name = models.CharField(max_length=100, null=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created']),
        ]
        verbose_name_plural = "Appliances"

    def __str__(self) -> str:
        return self.name

class Calculation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    total_load = models.FloatField(default=0, editable= False)

    inverter_rating = models.FloatField(editable=False, default=0)

    backup_time = models.PositiveIntegerField(null=False, default=2, help_text="How many hours of backup you need during a power outage.", validators= [validate_backup_time])

    battery_capacity = models.PositiveIntegerField(null=False, default=150, validators=[validate_battery_capacity], choices=BATTERY_CAPACITY_CHOICES)

    system_voltage= models.PositiveIntegerField(null=False, default=0, choices=BATTERY_VOLTAGE_CHOICES)

    total_battery_capacity= models.FloatField(editable=False, default=0)

    numbers_of_batteries = models.PositiveIntegerField(editable=False, default=0)

    total_solar_panel_capacity_needed = models.FloatField(editable=False, default=0)

    solar_panel_watt= models.PositiveIntegerField(null=False, default=300, choices=SOLAR_PANEL_WATT)

    numbers_of_solar_panel= models.IntegerField(editable=False, default=0)
    
    total_current= models.FloatField(editable=False, default=0)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created'])
        ]
        verbose_name_plural = "Calculations"

    def __str__(self) -> str:
        return str(self.id)

    def perform_calculations(self):
        items = self.calc.all()
        calc_utility = SystemCalculationUtility(
            total_load=self.total_load,
            backup_time=self.backup_time,
            battery_capacity=self.battery_capacity,
            system_voltage=self.system_voltage,
            solar_panel_watt=self.solar_panel_watt,
            items= items
        )
        
        calc_utility.perform_all_calculations()

        # Set model fields from calculation utility results
        self.total_load = calc_utility.calculate_total_load()
        self.inverter_rating = calc_utility.inverter_rating
        self.total_battery_capacity = calc_utility.total_battery_capacity
        self.numbers_of_batteries = calc_utility.numbers_of_batteries
        self.total_solar_panel_capacity_needed = calc_utility.total_solar_panel_capacity_needed
        self.numbers_of_solar_panel = calc_utility.numbers_of_solar_panel
        self.total_current = calc_utility.total_current

        self.save()





class CalculationItem(models.Model):
    calculation = models.ForeignKey(Calculation, related_name='calc', on_delete=models.CASCADE)
    appliance = models.ForeignKey(Appliance, related_name='items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    power_rating = models.PositiveIntegerField(default=1, validators=[validate_power_rating])

    def __str__(self) -> str:
        return f'{self.appliance.name} ({self.quantity} x {self.power_rating}W)'