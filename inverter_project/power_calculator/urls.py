
from django.urls import path
from .views import CalculationCreateView

urlpatterns = [
    path('calculate/', CalculationCreateView.as_view(), name='calculation-create'),
]
