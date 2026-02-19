from django.urls import path

from . import views

app_name = 'sales'

urlpatterns = [
    path('tables/', views.tables_list, name='tables'),
    path('tables/plan/', views.tables_list, name='tables_plan'),
    path('tables/new/', views.tables_new, name='tables_new'),
    path('tables/transfer/', views.tables_transfer, name='tables_transfer'),
    path('tables/<int:pk>/', views.table_detail, name='table_detail'),
    path('tables/<int:pk>/edit/', views.tables_edit, name='tables_edit'),
    path('tables/<int:pk>/delete/', views.tables_delete, name='tables_delete'),
    path('orders/', views.orders_list, name='orders'),
    path('orders/new/', views.orders_new, name='orders_new'),
    path('orders/<int:pk>/edit/', views.orders_edit, name='orders_edit'),
    path('orders/<int:pk>/delete/', views.orders_delete, name='orders_delete'),
    path('orders/<int:pk>/status/<str:status>/', views.order_status, name='order_status'),
    path('payments/', views.payments, name='payments'),
    path('payments/new/', views.payments_new, name='payments_new'),
    path('invoices/', views.invoices, name='invoices'),
]
