from django.shortcuts import render
from django.views.generic import TemplateView
from menu.models import Dish, Category

class HomeView(TemplateView):
    template_name = "public/home.html"


def menu_view(request):
    categories = Category.objects.filter(is_active=True)
    dishes = Dish.objects.filter(is_active=True).select_related("category").prefetch_related("options")
    q = request.GET.get("q", "").strip()
    cat = request.GET.get("category")
    min_price = request.GET.get("min")
    max_price = request.GET.get("max")
    sort = request.GET.get("sort")
    if q:
        dishes = dishes.filter(name__icontains=q)
    if cat:
        dishes = dishes.filter(category_id=cat)
    if min_price:
        dishes = dishes.filter(price__gte=min_price)
    if max_price:
        dishes = dishes.filter(price__lte=max_price)
    if sort == "price_asc":
        dishes = dishes.order_by("price")
    if sort == "price_desc":
        dishes = dishes.order_by("-price")
    return render(
        request,
        "public/menu.html",
        {
            "categories": categories,
            "dishes": dishes,
            "q": q,
            "cat": cat,
            "min_price": min_price or "",
            "max_price": max_price or "",
            "sort": sort or "",
        },
    )


def dish_detail(request, pk):
    dish = Dish.objects.select_related("category").prefetch_related("options").filter(pk=pk, is_active=True).first()
    return render(request, "public/dish_detail.html", {"dish": dish})


def delivery_track(request, pk):
    from orders.models import Order
    order = Order.objects.filter(pk=pk, order_type=Order.TYPE_DELIVERY).select_related("delivery_address", "assigned_delivery").first()
    return render(request, "public/delivery_track.html", {"order": order})


class SimplePage(TemplateView):
    template_name = "public/home.html"
