from django.urls import path
from .views import ApplianceListView, PerformCalculationView

urlpatterns = [
    path('appliances/', ApplianceListView.as_view(),name= 'appliance_list'),
    path('calculate/', PerformCalculationView.as_view(), name='calculation-create'),
    

]