from django.urls import path
from . import views

app_name = "tables"

urlpatterns = [
    path("", views.TablePlanView.as_view(), name="plan"),
    path("list/", views.TableListView.as_view(), name="list"),
    path("new/", views.TableCreateView.as_view(), name="new"),
    path("<int:pk>/", views.TableDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.TableUpdateView.as_view(), name="edit"),
    path("transfer/", views.TableTransferView.as_view(), name="transfer"),
    path("reservations/", views.TableReservationsView.as_view(), name="reservations"),
]
