from django.contrib import messages
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import TemplateView

from accounts.models import CustomerProfile, Address
from menu.models import Dish, Category
from orders.models import Order, OrderItem

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
    order = Order.objects.filter(pk=pk, order_type=Order.TYPE_DELIVERY).select_related("delivery_address", "assigned_delivery").first()
    return render(request, "public/delivery_track.html", {"order": order})


def _get_cart(request):
    return request.session.get("cart", {})


def _save_cart(request, cart):
    request.session["cart"] = cart
    request.session.modified = True


def cart_view(request):
    cart = _get_cart(request)
    dish_ids = cart.keys()
    dishes = Dish.objects.filter(id__in=dish_ids)
    items = []
    total = 0
    for dish in dishes:
        qty = int(cart.get(str(dish.id), 0))
        line_total = dish.price * qty
        total += line_total
        items.append({"dish": dish, "qty": qty, "line_total": line_total})
    return render(request, "public/cart.html", {"items": items, "total": total})


def cart_add(request, pk):
    dish = get_object_or_404(Dish, pk=pk, is_active=True)
    if dish.availability != Dish.AVAILABILITY_IN_STOCK:
        messages.error(request, "Ce plat est indisponible.")
        return redirect("public:menu")
    cart = _get_cart(request)
    key = str(dish.id)
    cart[key] = int(cart.get(key, 0)) + 1
    _save_cart(request, cart)
    messages.success(request, f"{dish.name} ajouté au panier.")
    return redirect(request.META.get("HTTP_REFERER", "public:menu"))


def cart_update(request, pk):
    cart = _get_cart(request)
    key = str(pk)
    qty = int(request.POST.get("qty", 1))
    if qty <= 0:
        cart.pop(key, None)
    else:
        cart[key] = qty
    _save_cart(request, cart)
    return redirect("public:cart")


def cart_remove(request, pk):
    cart = _get_cart(request)
    cart.pop(str(pk), None)
    _save_cart(request, cart)
    return redirect("public:cart")


def checkout_view(request):
    cart = _get_cart(request)
    if not cart:
        messages.error(request, "Votre panier est vide.")
        return redirect("public:menu")

    if request.method == "POST":
        order_type = request.POST.get("order_type", Order.TYPE_DELIVERY)
        name = request.POST.get("name", "")
        phone = request.POST.get("phone", "")
        address_line = request.POST.get("address", "")
        note = request.POST.get("note", "")

        order = Order.objects.create(
            order_type=order_type,
            status=Order.STATUS_PENDING,
            customer=request.user if request.user.is_authenticated else None,
            note=note,
        )

        if request.user.is_authenticated:
            profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
            order.customer_profile = profile
            if phone:
                profile.phone = phone
                profile.save(update_fields=["phone"])
            if order_type == Order.TYPE_DELIVERY and address_line:
                addr = Address.objects.create(
                    profile=profile,
                    label="Adresse livraison",
                    details=address_line,
                    is_default=True,
                )
                order.delivery_address = addr
        order.save()

        dishes = Dish.objects.filter(id__in=cart.keys())
        total = 0
        for dish in dishes:
            qty = int(cart.get(str(dish.id), 0))
            if qty <= 0:
                continue
            line_total = dish.price * qty
            total += line_total
            OrderItem.objects.create(
                order=order,
                dish=dish,
                quantity=qty,
                unit_price=dish.price,
                line_total=line_total,
            )
        order.total_amount = total
        order.save(update_fields=["total_amount"])

        _save_cart(request, {})
        messages.success(request, "Commande envoyée.")
        return redirect("public:order_detail", pk=order.id)

    return render(request, "public/checkout.html")


def orders_list(request):
    qs = Order.objects.order_by("-created_at")
    if request.user.is_authenticated:
        profile = CustomerProfile.objects.filter(user=request.user).first()
        qs = qs.filter(models.Q(customer=request.user) | models.Q(customer_profile=profile))
    else:
        qs = qs.none()
    return render(request, "public/orders.html", {"orders": qs})


def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    items = order.items.select_related("dish")
    return render(request, "public/order_detail.html", {"order": order, "items": items})


class SimplePage(TemplateView):
    template_name = "public/home.html"
