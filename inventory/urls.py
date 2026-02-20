from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("stock/", views.StockListView.as_view(), name="stock"),
    path("stock/new/", views.IngredientCreateView.as_view(), name="stock_new"),
    path("stock/<int:pk>/edit/", views.IngredientUpdateView.as_view(), name="stock_edit"),
    path("movements/", views.StockMovementsView.as_view(), name="movements"),
    path("movements/new/", views.StockMovementCreateView.as_view(), name="movement_new"),
    path("alerts/", views.StockAlertsView.as_view(), name="alerts"),
]
