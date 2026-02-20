from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from .forms import CategoryForm, DishForm, DishOptionForm
from .models import Category, Dish, DishOption
from orders.utils import is_manager


def list_view(request):
    if not is_manager(request.user):
        messages.error(request, "Accès refusé.")
        return redirect("public:home")
    categories = Category.objects.filter(is_active=True)
    q = request.GET.get("q", "").strip()
    cat = request.GET.get("category")
    status = request.GET.get("status")
    availability = request.GET.get("availability")
    dishes = Dish.objects.select_related("category").all().order_by("name")
    if q:
        dishes = dishes.filter(name__icontains=q)
    if cat:
        dishes = dishes.filter(category_id=cat)
    if status == "active":
        dishes = dishes.filter(is_active=True)
    if status == "inactive":
        dishes = dishes.filter(is_active=False)
    if availability:
        dishes = dishes.filter(availability=availability)
    paginator = Paginator(dishes, 12)
    page = request.GET.get("page")
    page_obj = paginator.get_page(page)
    return render(
        request,
        "menu/list.html",
        {
            "categories": categories,
            "dishes": page_obj,
            "q": q,
            "cat": cat,
            "status": status or "",
            "availability": availability or "",
            "page_obj": page_obj,
        },
    )


def product_detail(request, pk):
    if not is_manager(request.user):
        messages.error(request, "Accès refusé.")
        return redirect("public:home")
    dish = get_object_or_404(Dish, pk=pk, is_active=True)
    return render(request, "menu/product_detail.html", {"dish": dish})


def product_new(request):
    if not is_manager(request.user):
        messages.error(request, "Accès refusé.")
        return redirect("public:home")
    if request.method == "POST":
        form = DishForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("menu:list")
    else:
        form = DishForm()
    return render(request, "menu/product_form.html", {"form": form, "create": True})


def product_edit(request, pk):
    if not is_manager(request.user):
        messages.error(request, "Accès refusé.")
        return redirect("public:home")
    dish = get_object_or_404(Dish, pk=pk)
    if request.method == "POST":
        form = DishForm(request.POST, request.FILES, instance=dish)
        if form.is_valid():
            form.save()
            return redirect("menu:list")
    else:
        form = DishForm(instance=dish)
    return render(request, "menu/product_form.html", {"form": form, "create": False, "dish": dish})


def categories_view(request):
    if not is_manager(request.user):
        messages.error(request, "Accès refusé.")
        return redirect("public:home")
    categories = Category.objects.all().order_by("name")
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("menu:categories")
    else:
        form = CategoryForm()
    return render(request, "menu/categories.html", {"categories": categories, "form": form})


def options_view(request):
    if not is_manager(request.user):
        messages.error(request, "Accès refusé.")
        return redirect("public:home")
    q = request.GET.get("q", "").strip()
    options = DishOption.objects.select_related("dish").all().order_by("name")
    if q:
        options = options.filter(name__icontains=q)
    if request.method == "POST":
        form = DishOptionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("menu:options")
    else:
        form = DishOptionForm()
    paginator = Paginator(options, 12)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "menu/options.html", {"options": page_obj, "form": form, "q": q, "page_obj": page_obj})
