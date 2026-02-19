from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.core.paginator import Paginator

from .forms import CategoryForm, DishForm
from .models import Category, Dish, DishVariant


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
    categories = Category.objects.all().order_by('name')
    q = request.GET.get('q', '').strip()
    cat = request.GET.get('category')
    dishes = Dish.objects.select_related('category').all().order_by('name')
    if q:
        dishes = dishes.filter(name__icontains=q)
    if cat:
        dishes = dishes.filter(category_id=cat)
    paginator = Paginator(dishes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        'menu/dishes_list.html',
        {
            'dishes': page_obj.object_list,
            'page_obj': page_obj,
            'categories': categories,
            'q': q,
            'cat': cat,
        },
    )


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


def options_list(request):
    variants = DishVariant.objects.select_related('dish').all().order_by('name')
    q = request.GET.get('q', '').strip()
    if q:
        variants = variants.filter(name__icontains=q)
    paginator = Paginator(variants, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        'menu/options_list.html',
        {
            'variants': page_obj.object_list,
            'page_obj': page_obj,
            'q': q,
        },
    )
