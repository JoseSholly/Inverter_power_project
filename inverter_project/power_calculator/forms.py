from django import forms
from .models import Appliance


class ApplianceForm(forms.ModelForm):
    class Meta:
        model= Appliance
        fields= [
            'name',
            'quantity',
            'power_rating',
            "backup_time"
        ]