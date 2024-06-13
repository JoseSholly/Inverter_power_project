from django.db import models
from .validator import validate_battery_capacity, validate_power_rating
import uuid
from math import ceil
import sympy as sp
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

    backup_time = models.BigIntegerField(null=False, default=2, help_text="How many hours of backup you need during a power outage.")

    battery_capacity = models.BigIntegerField(null=False, default=150, validators=[validate_battery_capacity], choices=BATTERY_CAPACITY_CHOICES)

    battery_voltage= models.IntegerField(null=False, default=0, choices=BATTERY_VOLTAGE_CHOICES)

    total_battery_capacity= models.FloatField(editable=False, default=0)

    numbers_of_batteries = models.BigIntegerField(editable=False, default=0)

    total_solar_panel_capacity_needed = models.FloatField(editable=False, default=0)

    solar_panel_watt= models.IntegerField(null=False, default=300, choices=SOLAR_PANEL_WATT)

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

    def calculate_total_load(self):
        total_load = sum(item.power_rating * item.quantity for item in self.calc.all())
        self.total_load = total_load
        self.save()
        return total_load
    
    def calculate_total_inverter_rating(self):
        pf= 0.8 #Power factor
        inverter_rating = self.total_load / pf  
        self.inverter_rating= inverter_rating
        self.save()
        return inverter_rating

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
        return numbers_of_battery
    
    def calculate_solar_panel_capacity_needed(self):
        total_energy_req_KWH= (self.total_load * self.backup_time) / 1000
        aveage_peak_sun_hour= 5
        total_solar_panel_capacity= round((total_energy_req_KWH / aveage_peak_sun_hour)  * 1000)
        # Adjusting Total solar capacity for system loss: Diving total panel cap by inverter efficiency
        inverter_eff= 0.8
        adj_total_solar_panel_capacity= total_solar_panel_capacity / inverter_eff
        self.total_solar_panel_capacity_needed= adj_total_solar_panel_capacity
        self.save()
        return adj_total_solar_panel_capacity

    def get_no_panel(self,required_capacity, panel_capacity):
        """
        Function solve the inequality equation to get number greater than needed solar capacity
        """
        x = sp.symbols('x')
        inequality= x * panel_capacity > required_capacity
        solution= sp.solve(inequality, x)
    
        if solution:
            solution= solution.args[0]
            solution= solution.lhs.evalf()
        else:
            # Handle case where no solution found (though should not typically occur)
            solution = 0
        return solution
    
    def calculate_no_of_panel(self):
        numbers_of_solar_panel= self.get_no_panel(required_capacity=self.total_solar_panel_capacity_needed, panel_capacity=self.solar_panel_watt)

        numbers_of_solar_panel= round(ceil(numbers_of_solar_panel))

        self.numbers_of_solar_panel = numbers_of_solar_panel
        self.save()
        return numbers_of_solar_panel
    
    def calculate_total_current(self):
        total_solar_panel_wattage= self.numbers_of_solar_panel * self.solar_panel_watt
        """
         The charge controller should be able to handle the total current produced by the solar panels. It's also advisable to add a safety margin of around 25%.
        """
        total_current= (total_solar_panel_wattage / self.battery_voltage) * 1.25 # Add buffer
        self.total_current= total_current
        self.save()
        return total_current






class CalculationItem(models.Model):
    calculation = models.ForeignKey(Calculation, related_name='calc', on_delete=models.CASCADE)
    appliance = models.ForeignKey(Appliance, related_name='items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    power_rating = models.PositiveIntegerField(default=1, validators=[validate_power_rating])

    def __str__(self) -> str:
        return f'{self.appliance.name} ({self.quantity} x {self.power_rating}W)'