from django.urls import path

from . import views

app_name = 'reservations'

urlpatterns = [
    path('', views.list_view, name='list'),
    path('new/', views.reservation_new, name='new'),
    path('<int:pk>/edit/', views.reservation_edit, name='edit'),
    path('<int:pk>/delete/', views.reservation_delete, name='delete'),
]
