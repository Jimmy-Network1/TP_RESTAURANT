from django.urls import path

from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('export/sales/', views.export_sales_csv, name='export_sales'),
    path('export/payments/', views.export_payments_csv, name='export_payments'),
]
