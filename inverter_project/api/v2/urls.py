from django.urls import path
from .views import AppliancesListView

urlpatterns = [
    path('appliances/', AppliancesListView.as_view(),name= 'appliance_list')
]