from django.urls import path
from .views import AppliancesListView, CalculationCreateView, CalculationsListView

urlpatterns = [
    path('appliances/', AppliancesListView.as_view(),name= 'appliance_list'),
    path('calculate/', CalculationCreateView.as_view(), name='calculation-create'),
    path('calculations-list/', CalculationsListView.as_view(), name='calculation-list'),

]