from django.core.exceptions import ValidationError


def validate_battery_capacity(value):
    if value < 150 or value > 250:
        raise ValidationError("Battery capacity must be between 150 and 220.")
    else:
        return value

def validate_power_rating(value):
    if value<1:
        raise ValidationError("Power capacity must be greater than 1")
    else:
        return value

def validate_backup_time(value):
    if value<1:
        raise ValidationError("Backup Time must be greater than 1 hour")
    else:
        return value


    