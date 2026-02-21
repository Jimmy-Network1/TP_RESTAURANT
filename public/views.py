from django.contrib import messages
from decimal import Decimal
from django.db import transaction
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.views.generic import TemplateView
import re

from accounts.models import CustomerProfile, Address
from accounts.notifications import notify_order_status, create_notification
from menu.models import Dish, Category
from inventory.models import Ingredient, StockMovement, InventoryAlert
from orders.models import Order, OrderItem
from tablesapp.models import Table

class HomeView(TemplateView):
    template_name = "public/home.html"

def _dish_available(dish):
    if not dish or not dish.is_active:
        return False
    if dish.availability != Dish.AVAILABILITY_IN_STOCK:
        return False
    ingredient = Ingredient.objects.filter(name__iexact=dish.name, is_active=True).first()
    if ingredient and ingredient.quantity_in_stock <= 0:
        return False
    return True


def _maybe_alert(ingredient, old_qty, new_qty, user):
    if ingredient.alert_threshold and ingredient.alert_threshold > 0:
        if old_qty > ingredient.alert_threshold and new_qty <= ingredient.alert_threshold:
            alert = InventoryAlert.objects.create(
                ingredient=ingredient,
                message=f"Stock faible: {ingredient.name} ({new_qty} {ingredient.get_unit_display()})",
                created_by=user if user.is_authenticated else None,
            )
            create_notification(
                target_role="manager",
                message=alert.message,
                url="/inventory/stock/",
                level="warn",
            )


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
    for d in dishes:
        d.can_order = _dish_available(d)
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
    if dish:
        dish.can_order = _dish_available(dish)
    return render(request, "public/dish_detail.html", {"dish": dish})


def delivery_track(request, pk):
    order = Order.objects.filter(pk=pk, order_type=Order.TYPE_DELIVERY).select_related("delivery_address", "assigned_delivery").first()
    if not order:
        return render(request, "public/delivery_track.html", {"order": None})
    if request.user.is_authenticated:
        profile = CustomerProfile.objects.filter(user=request.user).first()
        if order.customer_id != request.user.id and order.customer_profile_id != (profile.id if profile else None):
            messages.error(request, "Accès refusé.")
            return redirect("public:home")
    return render(request, "public/delivery_track.html", {"order": order})


def _get_cart(request):
    return request.session.get("cart", {})


def _save_cart(request, cart):
    request.session["cart"] = cart
    request.session.modified = True


def _cart_summary(cart):
    dish_ids = list(cart.keys())
    dishes = Dish.objects.filter(id__in=dish_ids)
    total = Decimal("0")
    items = {}
    for dish in dishes:
        qty = int(cart.get(str(dish.id), 0))
        if qty <= 0:
            continue
        line_total = dish.price * qty
        total += line_total
        items[str(dish.id)] = {
            "qty": qty,
            "line_total": str(line_total),
        }
    count = sum(int(v) for v in cart.values())
    return {"count": count, "total": str(total), "items": items, "empty": count == 0}


def cart_view(request):
    cart = _get_cart(request)
    dish_ids = cart.keys()
    dishes = Dish.objects.filter(id__in=dish_ids)
    items = []
    total = 0
    has_unavailable = False
    for dish in dishes:
        qty = int(cart.get(str(dish.id), 0))
        line_total = dish.price * qty
        total += line_total
        available = _dish_available(dish)
        if not available:
            has_unavailable = True
        items.append({"dish": dish, "qty": qty, "line_total": line_total, "available": available})
    return render(request, "public/cart.html", {"items": items, "total": total, "has_unavailable": has_unavailable})


def cart_add(request, pk):
    dish = get_object_or_404(Dish, pk=pk, is_active=True)
    if not _dish_available(dish):
        messages.error(request, "Ce plat est indisponible.")
        return redirect("public:menu")
    ingredient = Ingredient.objects.filter(name__iexact=dish.name, is_active=True).first()
    cart = _get_cart(request)
    key = str(dish.id)
    new_qty = int(cart.get(key, 0)) + 1
    if ingredient and ingredient.quantity_in_stock < new_qty:
        messages.error(request, "Stock insuffisant.")
        return redirect(request.META.get("HTTP_REFERER", "public:menu"))
    cart[key] = new_qty
    _save_cart(request, cart)
    messages.success(request, f"{dish.name} ajouté au panier.")
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(_cart_summary(cart))
    return redirect(request.META.get("HTTP_REFERER", "public:menu"))


def cart_update(request, pk):
    cart = _get_cart(request)
    dish = Dish.objects.filter(pk=pk, is_active=True).first()
    key = str(pk)
    action = request.POST.get("action")
    if action in {"inc", "dec"}:
        current = int(cart.get(key, 0))
        qty = current + 1 if action == "inc" else max(0, current - 1)
    else:
        qty = int(request.POST.get("qty", 1))
    if dish and qty > 0 and not _dish_available(dish):
        messages.error(request, f"{dish.name} est indisponible.")
        return redirect("public:cart")
    ingredient = Ingredient.objects.filter(name__iexact=dish.name, is_active=True).first() if dish else None
    if ingredient and qty > ingredient.quantity_in_stock:
        messages.error(request, "Stock insuffisant.")
        return redirect("public:cart")
    if qty <= 0:
        cart.pop(key, None)
    else:
        cart[key] = qty
    _save_cart(request, cart)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(_cart_summary(cart))
    return redirect("public:cart")


def cart_remove(request, pk):
    cart = _get_cart(request)
    cart.pop(str(pk), None)
    _save_cart(request, cart)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(_cart_summary(cart))
    return redirect("public:cart")


def cart_summary(request):
    cart = _get_cart(request)
    return JsonResponse(_cart_summary(cart))


def checkout_view(request):
    cart = _get_cart(request)
    if not cart:
        messages.error(request, "Votre panier est vide.")
        return redirect("public:menu")

    if request.method == "POST":
        dishes = Dish.objects.filter(id__in=cart.keys())
        for dish in dishes:
            if not _dish_available(dish):
                messages.error(request, f"{dish.name} est indisponible. Veuillez le retirer du panier.")
                return redirect("public:cart")
            ingredient = Ingredient.objects.filter(name__iexact=dish.name, is_active=True).first()
            if ingredient:
                qty = int(cart.get(str(dish.id), 0))
                if ingredient.quantity_in_stock < qty:
                    messages.error(request, f"Stock insuffisant pour {dish.name}.")
                    return redirect("public:cart")
        order_type = request.POST.get("order_type", Order.TYPE_DELIVERY)
        name = (request.POST.get("name", "") or "").strip()
        phone = (request.POST.get("phone", "") or "").strip()
        address_line = request.POST.get("address", "")
        table_number = request.POST.get("table_number", "")
        note = request.POST.get("note", "")

        if name and not re.fullmatch(r"[A-Za-z\s'\-]+", name):
            messages.error(request, "Nom invalide.")
            return redirect("public:checkout")
        if phone:
            normalized = re.sub(r"[\s\-]", "", phone)
            if not re.fullmatch(r"\+?\d{6,15}", normalized):
                messages.error(request, "Numéro de téléphone invalide.")
                return redirect("public:checkout")
            phone = normalized

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    order_type=order_type,
                    status=Order.STATUS_PENDING,
                    customer=request.user if request.user.is_authenticated else None,
                    note=note,
                )

                if order_type == Order.TYPE_DINE_IN:
                    if not table_number:
                        messages.error(request, "Numéro de table requis pour sur place.")
                        return redirect("public:checkout")
                    table = Table.objects.filter(name__iexact=table_number).first()
                    if not table:
                        messages.error(request, "Table introuvable.")
                        return redirect("public:checkout")
                    if table.status != Table.STATUS_FREE:
                        messages.error(request, "Cette table est déjà occupée.")
                        return redirect("public:checkout")
                    order.table = table

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

                total = Decimal("0")
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
                    ingredient = Ingredient.objects.filter(name__iexact=dish.name, is_active=True).first()
                    if ingredient:
                        old_qty = ingredient.quantity_in_stock
                        new_qty = old_qty - qty
                        if new_qty < 0:
                            raise ValueError(f"Stock insuffisant pour {dish.name}.")
                        ingredient.quantity_in_stock = new_qty
                        ingredient.save(update_fields=["quantity_in_stock"])
                        StockMovement.objects.create(
                            ingredient=ingredient,
                            movement_type=StockMovement.TYPE_OUT,
                            quantity=qty,
                            note=f"Vente commande #{order.id}",
                            created_by=request.user if request.user.is_authenticated else None,
                        )
                        _maybe_alert(ingredient, old_qty, new_qty, request.user)

                order.total_amount = total
                order.save(update_fields=["total_amount"])
                notify_order_status(order, order.status)
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect("public:cart")

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
    if request.user.is_authenticated:
        profile = CustomerProfile.objects.filter(user=request.user).first()
        if order.customer_id != request.user.id and order.customer_profile_id != (profile.id if profile else None):
            messages.error(request, "Accès refusé.")
            return redirect("public:orders")
    items = order.items.select_related("dish")
    return render(request, "public/order_detail.html", {"order": order, "items": items})


class SimplePage(TemplateView):
    template_name = "public/home.html"
