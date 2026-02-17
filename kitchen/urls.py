from django.urls import path

from . import views

app_name = 'kitchen'

urlpatterns = [
    path('board/', views.board, name='board'),
]
