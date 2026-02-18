from django.urls import path

from . import public_views as views

app_name = 'public'

urlpatterns = [
    path('', views.home, name='home'),
    path('menu/', views.menu_list, name='menu'),
    path('menu/<int:pk>/', views.dish_detail, name='dish_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('confirmation/', views.order_confirm_view, name='order_confirm'),
    path('reservations/', views.reservation_form, name='reservations'),
]
