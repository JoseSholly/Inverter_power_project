from django import forms
from .models import Appliance


class CalculationForm(forms.ModelForm):

    class Meta:
        model= Appliance
        fields= [
            'name',
            'quantity',
            'power_rating',
        ]