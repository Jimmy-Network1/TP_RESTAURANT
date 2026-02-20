from django.urls import path
from . import views

app_name = "public"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("menu/", views.menu_view, name="menu"),
    path("menu/<int:pk>/", views.dish_detail, name="menu_detail"),
    path("cart/", views.SimplePage.as_view(template_name="public/cart.html"), name="cart"),
    path("checkout/", views.SimplePage.as_view(template_name="public/checkout.html"), name="checkout"),
    path("orders/", views.SimplePage.as_view(template_name="public/orders.html"), name="orders"),
    path("orders/<int:pk>/", views.SimplePage.as_view(template_name="public/order_detail.html"), name="order_detail"),
    path("deliveries/track/<int:pk>/", views.delivery_track, name="delivery_track"),
    path("deliveries/history/", views.SimplePage.as_view(template_name="public/delivery_history.html"), name="delivery_history"),
    path("reservations/", views.SimplePage.as_view(template_name="public/reservations.html"), name="reservations"),
    path("profile/", views.SimplePage.as_view(template_name="public/profile.html"), name="profile"),
]
