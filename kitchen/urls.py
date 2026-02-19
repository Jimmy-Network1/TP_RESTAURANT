from django.urls import path

from . import views

app_name = 'kitchen'

urlpatterns = [
    path('board/', views.board, name='board'),
    path('bar/', views.bar_board, name='bar'),
    path('ticket/<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('ticket/<int:pk>/status/<str:status>/', views.ticket_status, name='ticket_status'),
]
