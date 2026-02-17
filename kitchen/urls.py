from django.urls import path

from . import views

app_name = 'kitchen'

urlpatterns = [
    path('board/', views.board, name='board'),
    path('stations/', views.stations_list, name='stations'),
    path('stations/new/', views.stations_new, name='stations_new'),
    path('stations/<int:pk>/edit/', views.stations_edit, name='stations_edit'),
    path('stations/<int:pk>/delete/', views.stations_delete, name='stations_delete'),
    path('tickets/', views.tickets_list, name='tickets'),
    path('tickets/new/', views.tickets_new, name='tickets_new'),
    path('tickets/<int:pk>/edit/', views.tickets_edit, name='tickets_edit'),
    path('tickets/<int:pk>/delete/', views.tickets_delete, name='tickets_delete'),
    path('recipes/', views.recipes_list, name='recipes'),
    path('recipes/new/', views.recipes_new, name='recipes_new'),
    path('recipes/<int:pk>/edit/', views.recipes_edit, name='recipes_edit'),
    path('recipes/<int:pk>/delete/', views.recipes_delete, name='recipes_delete'),
]
