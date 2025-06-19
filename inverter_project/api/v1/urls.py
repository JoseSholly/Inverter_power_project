from .views import SolarCalculationAPIView, ApplianceListView
from django.urls import path
urlpatterns = [
    path('calculate/', SolarCalculationAPIView.as_view(), name='calculation-create'),
    path('appliances/', ApplianceListView.as_view(), name="appliances")
   
]