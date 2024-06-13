
from django.urls import path
from .views import CalculationCreateView, CalculationsListView

urlpatterns = [
    path('calculate/', CalculationCreateView.as_view(), name='calculation-create'),
    path('calculations-list/', CalculationsListView.as_view(), name='calculation-list'),
]
