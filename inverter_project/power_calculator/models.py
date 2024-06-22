from django.db import models
from .validators import validate_battery_capacity, validate_power_rating, validate_backup_time
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

    backup_time = models.BigIntegerField(null=False, default=2, help_text="How many hours of backup you need during a power outage.", validators= [validate_backup_time])

    battery_capacity = models.BigIntegerField(null=False, default=150, validators=[validate_battery_capacity], choices=BATTERY_CAPACITY_CHOICES)

    system_voltage= models.IntegerField(null=False, default=0, choices=BATTERY_VOLTAGE_CHOICES)

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
        """
        Computes the total load based on the power rating and quantity of each appliance associated with the calculation.
        """
        total_load = sum(item.power_rating * item.quantity for item in self.calc.all())
        self.total_load = total_load
        self.save()
        return total_load
    
    def calculate_total_inverter_rating(self):
        """
        Calculates the required inverter rating based on the total load and a power factor (0.8).
        """

        pf= 0.8 #Power factor
        inverter_rating = self.total_load / pf  
        self.inverter_rating= inverter_rating
        self.save()
        return inverter_rating

    def calculate_total_battery_capacity(self):
        """
         Determines the total battery capacity needed considering the adjusted total load, backup time, system voltage, and inverter efficiency.
        """
        inverter_eff= 0.8
        total_battery_capacity= (self.total_load * self.backup_time) / (self.system_voltage * inverter_eff)
        
        total_battery_capacity= round(total_battery_capacity, 2)
        # print(f"Total bat cap: {total_battery_capacity}")
        self.total_battery_capacity= total_battery_capacity
        self.save()
        return total_battery_capacity
    
    def calculate_no_of_battery(self):

        """
        Computes the number of batteries required based on the system voltage and battery capacity.
        """
        # tot_bat_cap= self.calculate_total_battery_capacity()
        individual_battery_volt= 12

        # Voltage is greater than 12V then system is  in series
        # print(f"total bat cap: {self.total_battery_capacity}")
        if self.system_voltage!=12:
            numbers_of_battery= ceil(self.system_voltage / individual_battery_volt)
            # print(f"Number of batteries in parallel:{numbers_of_battery}")
        else:
            numbers_of_battery= ceil(self.total_battery_capacity / self.battery_capacity)
            # print(f"Number of batteries in series:{numbers_of_battery}")
        self.numbers_of_batteries= numbers_of_battery
        self.save()
        return numbers_of_battery
    
    def calculate_solar_panel_capacity_needed(self):
        """
         Estimates the total solar panel capacity needed to meet energy requirements, considering average peak sun hours and inverter efficiency.
        """
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
        Uses SymPy to solve an inequality to determine the number of solar panels required.
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
        """
        Calculates the number of solar panels needed based on the solar panel wattage and the estimated solar panel capacity needed.
        """
        numbers_of_solar_panel= self.get_no_panel(required_capacity=self.total_solar_panel_capacity_needed, panel_capacity=self.solar_panel_watt)

        numbers_of_solar_panel= round(ceil(numbers_of_solar_panel))

        self.numbers_of_solar_panel = numbers_of_solar_panel
        self.save()
        return numbers_of_solar_panel
    
    def calculate_total_current(self):
        total_solar_panel_wattage= self.numbers_of_solar_panel * self.solar_panel_watt
        """ Computes the total current generated by the solar panels, accounting for the system voltage and adding a buffer.

         The charge controller should be able to handle the total current produced by the solar panels. It's also advisable to add a safety margin of around 25%.
        """
        total_current= round(total_solar_panel_wattage / self.system_voltage, 2) 
        
        # print(f"Total Current: {total_current}")
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