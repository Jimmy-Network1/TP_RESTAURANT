from django.urls import path
from . import views

app_name = "menu"

urlpatterns = [
    path("", views.list_view, name="list"),
    path("categories/", views.categories_view, name="categories"),
    path("options/", views.options_view, name="options"),
    path("product/new/", views.product_new, name="product_new"),
    path("product/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("product/<int:pk>/", views.product_detail, name="product_detail"),
]
