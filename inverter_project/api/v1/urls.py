from .views import SolarCalculationAPIView
from django.urls import path
urlpatterns = [
    path('calculate/', SolarCalculationAPIView.as_view(), name='calculation-create'),
   
]