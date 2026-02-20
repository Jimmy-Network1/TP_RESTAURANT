from django.urls import path
from . import views

app_name = "reservations"

urlpatterns = [
    path("", views.ClientReservationListView.as_view(), name="client_list"),
    path("new/", views.ClientReservationCreateView.as_view(), name="client_new"),
    path("<int:pk>/", views.ClientReservationDetailView.as_view(), name="client_detail"),
    path("staff/", views.StaffReservationListView.as_view(), name="staff_list"),
    path("staff/<int:pk>/", views.StaffReservationDetailView.as_view(), name="staff_detail"),
    path("staff/<int:pk>/checkin/", views.reservation_checkin, name="staff_checkin"),
]
