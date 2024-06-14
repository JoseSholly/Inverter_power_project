
from django.urls import path
from .views import CalculationCreateView, CalculationsListView, CalculationUpdateView

urlpatterns = [
    path('calculate/', CalculationCreateView.as_view(), name='calculation-create'),
    path('calculations-list/', CalculationsListView.as_view(), name='calculation-list'),
    path('calculation/<uuid:pk>/', CalculationUpdateView.as_view(), name='calculation-update'),
]
