from django.db import models
from .validator import validate_battery_capacity
import uuid

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
    battery_capacity = models.BigIntegerField(null=False, default=150, validators=[validate_battery_capacity])

    battery_voltage= models.BigIntegerField(null=False, default=0)

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
        self.inverter_rating = total_load * 1.25  # Adjust as per your formula
        self.save()

class CalculationItem(models.Model):
    calculation = models.ForeignKey(Calculation, related_name='calc', on_delete=models.CASCADE)
    appliance = models.ForeignKey(Appliance, related_name='items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    power_rating = models.PositiveIntegerField(default=1)

    def __str__(self) -> str:
        return f'{self.appliance.name} ({self.quantity} x {self.power_rating}W)'