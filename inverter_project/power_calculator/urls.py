from django.urls import path, include
from . import views
urlpatterns=[
    path('appliances/', views.ApplianceListCreateAPIView.as_view(), name='appliance-list-create'),
    path('inverter-power/', views.InverterPowerView.as_view(), name='inverter-power'),
]