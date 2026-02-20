from django.urls import path
from . import views

app_name = "delivery"

urlpatterns = [
    path("clients/", views.clients_list, name="clients"),
    path("dashboard/", views.courier_dashboard, name="dashboard"),
    path("deliveries/", views.deliveries_list, name="deliveries"),
    path("deliveries/<int:pk>/", views.delivery_detail, name="detail"),
    path("couriers/", views.couriers_view, name="couriers"),
    path("assign/", views.assign_view, name="assign"),
]
