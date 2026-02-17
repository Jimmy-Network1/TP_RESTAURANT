from django.urls import path

from . import views

app_name = 'inventory'

urlpatterns = [
    path('ingredients/', views.ingredients_list, name='ingredients'),
    path('ingredients/new/', views.ingredients_new, name='ingredients_new'),
    path('ingredients/<int:pk>/edit/', views.ingredients_edit, name='ingredients_edit'),
    path('ingredients/<int:pk>/delete/', views.ingredients_delete, name='ingredients_delete'),
    path('movements/', views.movements_list, name='movements'),
    path('movements/new/', views.movements_new, name='movements_new'),
    path('suppliers/', views.suppliers_list, name='suppliers'),
    path('suppliers/new/', views.suppliers_new, name='suppliers_new'),
    path('suppliers/<int:pk>/edit/', views.suppliers_edit, name='suppliers_edit'),
    path('suppliers/<int:pk>/delete/', views.suppliers_delete, name='suppliers_delete'),
    path('purchase-orders/', views.purchase_orders_list, name='purchase_orders'),
    path('purchase-orders/new/', views.purchase_orders_new, name='purchase_orders_new'),
    path('purchase-orders/<int:pk>/edit/', views.purchase_orders_edit, name='purchase_orders_edit'),
    path('purchase-orders/<int:pk>/delete/', views.purchase_orders_delete, name='purchase_orders_delete'),
]
