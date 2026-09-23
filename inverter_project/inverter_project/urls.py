"""Django URLconf. The REST API lives in inverter_project/api.py (django-bolt);
this only serves the admin site."""
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]
