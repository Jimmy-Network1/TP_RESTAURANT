from django.urls import path

from . import views

app_name = 'menu'

urlpatterns = [
    path('categories/', views.categories_list, name='categories'),
    path('categories/new/', views.categories_new, name='categories_new'),
    path('categories/<int:pk>/edit/', views.categories_edit, name='categories_edit'),
    path('categories/<int:pk>/delete/', views.categories_delete, name='categories_delete'),
    path('dishes/', views.dishes_list, name='dishes'),
    path('dishes/new/', views.dishes_new, name='dishes_new'),
    path('dishes/<int:pk>/edit/', views.dishes_edit, name='dishes_edit'),
    path('dishes/<int:pk>/delete/', views.dishes_delete, name='dishes_delete'),
    path('options/', views.options_list, name='options'),
]
