from django.db import models


class Appliance(models.Model):
    name = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created']),
        ]
        verbose_name_plural = "Appliances"

    def __str__(self) -> str:
        return self.name
