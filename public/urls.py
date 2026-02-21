from django.urls import path
from . import views

app_name = "public"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("menu/", views.menu_view, name="menu"),
    path("menu/<int:pk>/", views.dish_detail, name="menu_detail"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:pk>/", views.cart_add, name="cart_add"),
    path("cart/update/<int:pk>/", views.cart_update, name="cart_update"),
    path("cart/remove/<int:pk>/", views.cart_remove, name="cart_remove"),
    path("cart/summary/", views.cart_summary, name="cart_summary"),
    path("checkout/", views.checkout_view, name="checkout"),
    path("my/orders/", views.orders_list, name="orders"),
    path("my/orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("deliveries/track/<int:pk>/", views.delivery_track, name="delivery_track"),
    path("deliveries/history/", views.SimplePage.as_view(template_name="public/delivery_history.html"), name="delivery_history"),
    # reservations handled by reservations app
    # profile handled by accounts app / client dashboard
]
