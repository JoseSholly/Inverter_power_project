from django.db import models
import uuid
from power_calculator.models import Appliance
from .validators import validate_backup_time, validate_battery_capacity, validate_power_rating

# Create your models here.
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
class Calculation(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    system_voltage= models.PositiveIntegerField(null=False, default=0, choices=BATTERY_VOLTAGE_CHOICES)
    

    battery_capacity = models.PositiveIntegerField(null=False, default=150, choices=BATTERY_CAPACITY_CHOICES, validators=[validate_battery_capacity])

    solar_panel_watt= models.PositiveIntegerField(null=False, default=300, choices=SOLAR_PANEL_WATT)

    total_load = models.FloatField(default=0, editable= False)

    inverter_rating = models.FloatField(editable=False, default=0)

    total_battery_capacity= models.FloatField(editable=False, default=0)

    numbers_of_solar_panel= models.IntegerField(editable=False, default=0)

    controller_current= models.IntegerField(editable=False, default=0)


    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created'])
        ]
        verbose_name_plural = "Calculations"

    def __str__(self):
        return str(self.id)
    

class CalculationItem(models.Model):
    calculation = models.ForeignKey(Calculation, related_name='system_calc', on_delete=models.CASCADE)
    appliance = models.ForeignKey(Appliance, related_name='appliance', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    power_rating = models.PositiveIntegerField(default=0, validators= [validate_power_rating])
    backup_time = models.PositiveIntegerField(default=0, validators= [validate_backup_time])

    def __str__(self) -> str:
        return f'{self.appliance.name}: ({self.quantity} x {self.power_rating} x {self.backup_time} WH)'
