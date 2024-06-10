from django.db import models
from power_calculator.models import Appliance
import uuid
# Create your models here.


class Calculation(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4,
                          unique=True,
                          editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created'])
        ]

    def __str__(self) -> str:
        return f"{self.id}"


class CalculationItem(models.Model):
    calculation= models.ForeignKey(Calculation,
                              related_name='items',
                              on_delete=models.CASCADE)
    appliance= models.ForeignKey(Appliance,
                                related_name='calculation_items',
                                on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    power_rating= models.PositiveIntegerField(default=1, help_text= "Power rating in watts")

    def __str__(self) -> str:
        return str(self.id)
    
    @property
    def get_total_power(self):
        return self.quantity * self.power_rating
    

