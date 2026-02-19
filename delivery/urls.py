from django.urls import path

from . import views

app_name = 'delivery'

urlpatterns = [
    path('clients/', views.clients_list, name='clients'),
    path('clients/<str:phone>/', views.client_detail, name='client_detail'),
    path('deliveries/', views.deliveries_list, name='deliveries'),
    path('couriers/', views.couriers_list, name='couriers'),
    path('assign/', views.assign, name='assign'),
]
