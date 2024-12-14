from django.urls import path
from .views import AppliancesListView, CalculationCreateView, CalculationsListView, CalculationUpdateView

urlpatterns = [
    path('appliances/', AppliancesListView.as_view(),name= 'appliance_list'),
    path('calculate/', CalculationCreateView.as_view(), name='calculation-create'),
    path('calculations-list/', CalculationsListView.as_view(), name='calculation-list'),
    path('<uuid:pk>/update/', CalculationUpdateView.as_view(), name='calculation-update'),

]