from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("", views.ReportsDashboardView.as_view(), name="dashboard"),
    path("daily/", views.DailySalesView.as_view(), name="daily"),
    path("stats/", views.StatsView.as_view(), name="stats"),
    path("products/", views.TopProductsView.as_view(), name="products"),
    path("delivery/", views.DeliveryReportView.as_view(), name="delivery"),
    path("export/", views.ExportView.as_view(), name="export"),
]
