from django.urls import path
from . import views

app_name = "kitchen"

urlpatterns = [
    path("", views.KitchenBoardView.as_view(), name="board"),
    path("board/", views.KitchenBoardView.as_view(), name="board_alt"),
    path("bar/", views.KitchenBarView.as_view(), name="bar"),
    path("history/", views.KitchenHistoryView.as_view(), name="history"),
    path("ticket/<int:pk>/", views.KitchenTicketView.as_view(), name="ticket"),
    path("ticket/<int:pk>/action/", views.kitchen_action, name="action"),
]
