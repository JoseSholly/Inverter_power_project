from rest_framework import generics
from .models import Calculation
from .serializers import CalculationSerializer

class CalculationCreateView(generics.CreateAPIView):
    queryset = Calculation.objects.all()
    serializer_class = CalculationSerializer


class CalculationsListView(generics.ListAPIView):
    queryset= Calculation.objects.all()
    serializer_class= CalculationSerializer

class CalculationUpdateView(generics.UpdateAPIView):
    queryset = Calculation.objects.all()
    serializer_class = CalculationSerializer