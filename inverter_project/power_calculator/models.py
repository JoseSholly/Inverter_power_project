from django.db import models
from .validator import validate_battery_capacity, validate_power_rating
import uuid
from math import ceil
# Define the voltage choices
BATTERY_VOLTAGE_CHOICES = [
        (12, '12V'),
        (24, '24V'),
        (48, '48V'),
    ]

BATTERY_CAPACITY_CHOICES = [
        (150, '150Ah'),
        (200, '200Ah'),
        (220, '220Ah'),
        (250, '250Ah'),
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

    total_load = models.FloatField(null=False, default=0)

    inverter_rating = models.FloatField(null=False, default=0)

    backup_time = models.BigIntegerField(null=False, default=2, help_text="How many hours of backup you need during a power outage.")
    battery_capacity = models.BigIntegerField(null=False, default=150, validators=[validate_battery_capacity], choices=BATTERY_CAPACITY_CHOICES)

    battery_voltage= models.IntegerField(null=False, default=0, choices=BATTERY_VOLTAGE_CHOICES)

    total_battery_capacity= models.FloatField(null=False, default=0)

    numbers_of_batteries = models.BigIntegerField(null=False, default=0)

    total_solar_panel_capacity = models.FloatField(null=False, default=0)

    numbers_of_solar_panel= models.BigIntegerField(null=False, default=0)
    
    total_current= models.FloatField(null=False, default=0)

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

    def calculate_total_load(self):
        total_load = sum(item.power_rating * item.quantity for item in self.calc.all())
        self.total_load = total_load
        pf= 0.8 #Power factor
        self.inverter_rating = total_load / pf  
        self.save()

    def calculate_total_battery_capacity(self):
        inverter_eff= 0.8
        total_battery_capacity= round( (self.total_load * self.backup_time) / (self.battery_voltage * inverter_eff) )
        self.total_battery_capacity= total_battery_capacity
        self.save()
        return total_battery_capacity
    
    def calculate_no_of_battery(self):
        # tot_bat_cap= self.calculate_total_battery_capacity()
        tot_bat_cap= self.total_battery_capacity
        numbers_of_battery= ceil(tot_bat_cap / self.battery_capacity)
        self.numbers_of_batteries= numbers_of_battery
        self.save()
    
    
class CalculationItem(models.Model):
    calculation = models.ForeignKey(Calculation, related_name='calc', on_delete=models.CASCADE)
    appliance = models.ForeignKey(Appliance, related_name='items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    power_rating = models.PositiveIntegerField(default=1, validators=[validate_power_rating])

    def __str__(self) -> str:
        return f'{self.appliance.name} ({self.quantity} x {self.power_rating}W)'