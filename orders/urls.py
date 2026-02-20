from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("", views.list_view, name="list"),
    path("new/", views.new_view, name="new"),
    path("history/", views.history_view, name="history"),
    path("delivery/", views.delivery_view, name="delivery"),
    path("notifications/", views.notifications_view, name="notifications"),
    path("<int:pk>/", views.detail_view, name="detail"),
    path("<int:pk>/edit/", views.edit_view, name="edit"),
    path("<int:pk>/split/", views.split_view, name="split"),
]
