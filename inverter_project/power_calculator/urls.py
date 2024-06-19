
from django.urls import path
from .views import CalculationCreateView, CalculationsListView, CalculationUpdateView, CalculationDeleteView, AppliancesListView

urlpatterns = [
    path('calculate/', CalculationCreateView.as_view(), name='calculation-create'),
    path('calculations-list/', CalculationsListView.as_view(), name='calculation-list'),
    path('<uuid:pk>/update/', CalculationUpdateView.as_view(), name='calculation-update'),
    path('<uuid:pk>/delete/', CalculationDeleteView.as_view(), name='calculation-delete'),
    path("appliances/", AppliancesListView.as_view(), name="appliance-view"),
]
