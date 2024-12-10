from django.urls import path
from .views import AppliancesListView, CalculationCreateView

urlpatterns = [
    path('appliances/', AppliancesListView.as_view(),name= 'appliance_list'),
    path('calculate/', CalculationCreateView.as_view(), name='calculation-create'),
]