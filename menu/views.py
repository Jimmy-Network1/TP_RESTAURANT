from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import CategoryForm, DishForm
from .models import Category, Dish


def categories_list(request):
    categories = Category.objects.all().order_by('name')
    return render(request, 'menu/categories_list.html', {'categories': categories})


def categories_new(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('menu:categories')
    else:
        form = CategoryForm()
    return render(request, 'menu/categories_new.html', {'form': form})


def categories_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('menu:categories')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'menu/categories_edit.html', {'form': form, 'category': category})


def categories_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        return redirect('menu:categories')
    return render(request, 'menu/categories_delete.html', {'category': category})


def dishes_list(request):
    dishes = Dish.objects.select_related('category').all().order_by('name')
    return render(request, 'menu/dishes_list.html', {'dishes': dishes})


def dishes_new(request):
    if request.method == 'POST':
        form = DishForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('menu:dishes')
    else:
        form = DishForm()
    return render(request, 'menu/dishes_new.html', {'form': form})


def dishes_edit(request, pk):
    dish = get_object_or_404(Dish, pk=pk)
    if request.method == 'POST':
        form = DishForm(request.POST, request.FILES, instance=dish)
        if form.is_valid():
            form.save()
            return redirect('menu:dishes')
    else:
        form = DishForm(instance=dish)
    return render(request, 'menu/dishes_edit.html', {'form': form, 'dish': dish})


def dishes_delete(request, pk):
    dish = get_object_or_404(Dish, pk=pk)
    if request.method == 'POST':
        dish.delete()
        return redirect('menu:dishes')
    return render(request, 'menu/dishes_delete.html', {'dish': dish})
