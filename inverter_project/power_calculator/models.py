from django.db import models
from django.utils import timezone

# Create your models here.

class Appliance(models.Model):
    name= models.CharField(max_length=100, null=False)
    quantity= models.PositiveIntegerField(default=1, null=False, help_text="Numbers of appliance")
    power_rating= models.PositiveIntegerField(null=False, help_text= "Power rating in watts")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated']
        indexes = [
            models.Index(fields=['-updated']),]

    def __str__(self) -> str:
        return self.name

    @property
    def total_power(self):
        return self.power_rating * self.quantity
    
    def power_factor(self):
        pf= 0.9
        return pf


