from django.urls import path

from . import views

urlpatterns = [
    path('<int:pk>/status/<str:status>/', views.order_status, name='order_status'),
]
