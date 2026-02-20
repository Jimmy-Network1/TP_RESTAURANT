from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone

from accounts.models import CustomerProfile
from orders.models import Order, OrderItem, OrderStatusLog


def _courier_queryset():
    group = Group.objects.filter(name__iexact="Livreur").first()
    if group:
        return group.user_set.all()
    return User.objects.all()


def clients_list(request):
    clients = CustomerProfile.objects.annotate(order_count=Count("orders")).select_related("user")
    return render(request, "delivery/clients.html", {"clients": clients})


def deliveries_list(request):
    status = request.GET.get("status", "")
    q = request.GET.get("q", "")
    qs = Order.objects.filter(order_type=Order.TYPE_DELIVERY).select_related("customer", "delivery_address", "assigned_delivery")
    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(
            Q(id__icontains=q) | Q(customer__username__icontains=q)
        )

    counters = {
        "preparing": qs.filter(status=Order.STATUS_PREPARING).count(),
        "ready": qs.filter(status=Order.STATUS_READY).count(),
        "on_route": qs.filter(status=Order.STATUS_ON_ROUTE).count(),
        "done": qs.filter(status=Order.STATUS_DONE).count(),
    }
    return render(request, "delivery/deliveries.html", {"orders": qs, "status": status, "q": q, "counters": counters})


def delivery_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, order_type=Order.TYPE_DELIVERY)
    items = order.items.select_related("dish")
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "delivered" and order.status == Order.STATUS_ON_ROUTE:
            order.status = Order.STATUS_DONE
            order.save(update_fields=["status"])
            OrderStatusLog.objects.create(order=order, status=order.status, actor=request.user)
            messages.success(request, "Commande marquee livree.")
            return redirect("delivery:detail", pk=order.id)
        if action == "issue":
            reason = request.POST.get("reason", "").strip()[:200]
            OrderStatusLog.objects.create(order=order, status=order.status, actor=request.user, reason=reason)
            messages.warning(request, "Probleme enregistre.")
            return redirect("delivery:detail", pk=order.id)
    return render(request, "delivery/detail.html", {"order": order, "items": items})


def assign_view(request):
    ready_orders = Order.objects.filter(order_type=Order.TYPE_DELIVERY, status=Order.STATUS_READY).select_related("delivery_address")
    couriers_qs = _courier_queryset()
    couriers = []
    for c in couriers_qs:
        active = Order.objects.filter(assigned_delivery=c, status=Order.STATUS_ON_ROUTE).exists()
        couriers.append({"user": c, "status": "busy" if active else "free"})

    if request.method == "POST":
        order_id = request.POST.get("order_id")
        courier_id = request.POST.get("courier_id")
        order = Order.objects.filter(id=order_id, status=Order.STATUS_READY).first()
        courier = couriers_qs.filter(id=courier_id).first()
        if not order:
            messages.error(request, "Commande non prete.")
        elif not courier:
            messages.error(request, "Livreur invalide.")
        else:
            order.assigned_delivery = courier
            order.status = Order.STATUS_ON_ROUTE
            order.save(update_fields=["assigned_delivery", "status"])
            OrderStatusLog.objects.create(order=order, status=order.status, actor=request.user)
            messages.success(request, "Livreur attribue.")
            return redirect("delivery:deliveries")

    return render(request, "delivery/assign.html", {"orders": ready_orders, "couriers": couriers})


def couriers_view(request):
    couriers_qs = _courier_queryset()
    couriers = []
    for c in couriers_qs:
        active = Order.objects.filter(assigned_delivery=c, status=Order.STATUS_ON_ROUTE).exists()
        couriers.append({"user": c, "status": "busy" if active else "free"})
    return render(request, "delivery/couriers.html", {"couriers": couriers})
