from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .cache import invalidate_now_and_on_commit
from .models import Appliance


@receiver(post_save, sender=Appliance, dispatch_uid="appliance_cache_on_save")
@receiver(post_delete, sender=Appliance, dispatch_uid="appliance_cache_on_delete")
def invalidate_appliance_cache(**kwargs) -> None:
    invalidate_now_and_on_commit()
