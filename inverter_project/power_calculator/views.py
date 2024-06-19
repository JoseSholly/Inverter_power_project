from rest_framework import generics
from .models import Calculation, Appliance
from .serializers import CalculationSerializer, ApplianceSerializer
from rest_framework.response import Response
from .permissions import IsStaffUser

class CalculationCreateView(generics.CreateAPIView):
    queryset = Calculation.objects.all()
    serializer_class = CalculationSerializer

class CalculationsListView(generics.ListAPIView):
    queryset= Calculation.objects.all()
    serializer_class= CalculationSerializer

class CalculationUpdateView(generics.UpdateAPIView):
    queryset = Calculation.objects.all()
    serializer_class = CalculationSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

class CalculationDeleteView(generics.DestroyAPIView):
    queryset = Calculation.objects.all()
    serializer_class = CalculationSerializer

    def destroy(self, request, *args, **kwargs):
        
        instance = self.get_object()
        
        calculation_id = instance.id
        self.perform_destroy(instance)
        return Response({"message": f"Calculation {calculation_id} deleted successfully"})
    

class AppliancesListView(generics.ListAPIView):
    queryset= Appliance.objects.all()
    serializer_class= ApplianceSerializer

