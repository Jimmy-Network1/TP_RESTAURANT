from django.urls import path
from .views import DashboardView, ClientDashboardView

app_name = "dashboard"

urlpatterns = [
    path("", DashboardView.as_view(), name="home"),
    path("client/", ClientDashboardView.as_view(), name="client"),
]
