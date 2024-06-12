from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid

def validate_battery_capacity(value):
    if value < 150 or value > 230:
        raise ValidationError("Battery capacity must be between 150 and 220.")
    else:
        return value
# Create your models here.

# class Appliance(models.Model):
#     name= models.CharField(max_length=100, null=False)
#     quantity= models.PositiveIntegerField(default=1, null=False, help_text="Numbers of appliance")
#     power_rating= models.PositiveIntegerField(null=False, help_text= "Power rating in watts")
#     created = models.DateTimeField(auto_now_add=True)
#     updated = models.DateTimeField(auto_now=True)

#     class Meta:
#         ordering = ['-updated']
#         indexes = [
#             models.Index(fields=['-updated']),]

#     def __str__(self) -> str:
#         return self.name

#     @property
#     def total_power(self):
#         return self.power_rating * self.quantity
    
#     def power_factor(self):
#         pf= 0.9
#         return pf


class Calculation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
   
    total_load = models.FloatField(null=False)
    inverter_rating= models.FloatField(null=False)
    backup_time= models.BigIntegerField(null=False,default=2,  help_text="How many hours of backup you need during a power outage.")
    battery_capacity= models.BigIntegerField(null=False, default= 150, validators=[validate_battery_capacity])
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

