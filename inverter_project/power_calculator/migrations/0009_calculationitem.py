# Generated by Django 4.2.13 on 2024-06-12 18:58

from django.db import migrations, models
import django.db.models.deletion
import power_calculator.validator


class Migration(migrations.Migration):

    dependencies = [
        ('power_calculator', '0008_calculation_appliance'),
    ]

    operations = [
        migrations.CreateModel(
            name='CalculationItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_load', models.FloatField(default=0)),
                ('inverter_rating', models.FloatField(default=0)),
                ('backup_time', models.BigIntegerField(default=2, help_text='How many hours of backup you need during a power outage.')),
                ('battery_capacity', models.BigIntegerField(default=150, validators=[power_calculator.validator.validate_battery_capacity])),
                ('appliance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='power_calculator.appliance')),
                ('calculation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='calc', to='power_calculator.calculation')),
            ],
        ),
    ]
