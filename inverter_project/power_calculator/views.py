from rest_framework import generics
from .models import Calculation
from .serializers import CalculationSerializer
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

class CalculationCreateView(generics.CreateAPIView):
    queryset = Calculation.objects.all()
    serializer_class = CalculationSerializer


class CalculationsListView(generics.ListAPIView):
    queryset= Calculation.objects.all()
    serializer_class= CalculationSerializer

class CalculationUpdateView(generics.UpdateAPIView):
    queryset = Calculation.objects.all()
    serializer_class = CalculationSerializer

class CalculationDeleteView(generics.DestroyAPIView):
    queryset = Calculation.objects.all()
    serializer_class = CalculationSerializer

    def destroy(self, request, *args, **kwargs):
        
        instance = self.get_object()
        
        calculation_id = instance.id
        self.perform_destroy(instance)
        return Response({"message": f"Calculation {calculation_id} deleted successfully"})

