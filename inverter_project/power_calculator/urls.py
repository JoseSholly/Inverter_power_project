
from django.urls import path
from .views import CalculationCreateView, CalculationsListView, CalculationUpdateView, CalculationDeleteView

urlpatterns = [
    path('calculate/', CalculationCreateView.as_view(), name='calculation-create'),
    path('calculations-list/', CalculationsListView.as_view(), name='calculation-list'),
    path('calculation/<uuid:pk>/', CalculationUpdateView.as_view(), name='calculation-update'),
    path('calculation/<uuid:pk>/delete/', CalculationDeleteView.as_view(), name='calculation-delete'),
]
