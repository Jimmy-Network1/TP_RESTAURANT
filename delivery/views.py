from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone

from accounts.models import CustomerProfile
from orders.models import Order, OrderItem, OrderStatusLog
from orders.utils import can_transition, log_transition
from billing.models import CashSession
from billing.models import Payment


def _courier_queryset():
    group = Group.objects.filter(name__iexact="Livreur").first()
    if group:
        return group.user_set.all()
    return User.objects.all()

def _is_manager(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__iexact="gerant").exists() or user.groups.filter(name__iexact="manager").exists()

def _is_courier(user):
    if not user.is_authenticated:
        return False
    return user.groups.filter(name__iexact="livreur").exists()

def courier_required(user):
    return _is_courier(user) or _is_manager(user)


@login_required
def clients_list(request):
    if not _is_manager(request.user):
        return redirect("public:home")
    clients = CustomerProfile.objects.annotate(order_count=Count("orders")).select_related("user")
    return render(request, "delivery/clients.html", {"clients": clients})


@login_required
def deliveries_list(request):
    if not _is_manager(request.user):
        return redirect("public:home")
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


@login_required
def courier_dashboard(request):
    if not courier_required(request.user):
        return redirect("public:home")
    now = timezone.now()
    qs = Order.objects.filter(
        order_type=Order.TYPE_DELIVERY,
        assigned_delivery=request.user,
    ).select_related("customer", "delivery_address", "customer_profile")

    status = request.GET.get("status", "")
    if status in [Order.STATUS_READY, Order.STATUS_ON_ROUTE]:
        qs = qs.filter(status=status)

    active = qs.filter(status__in=[Order.STATUS_READY, Order.STATUS_ON_ROUTE]).order_by("created_at")
    history = qs.filter(status=Order.STATUS_DONE, updated_at__date=now.date()).order_by("-updated_at")[:6]

    counters = {
        "active": qs.filter(status__in=[Order.STATUS_READY, Order.STATUS_ON_ROUTE]).count(),
        "done_today": qs.filter(status=Order.STATUS_DONE, updated_at__date=now.date()).count(),
    }
    return render(request, "delivery/dashboard.html", {
        "orders": active,
        "history": history,
        "status": status,
        "counters": counters,
        "now": now,
    })


@login_required
def delivery_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, order_type=Order.TYPE_DELIVERY)
    if not courier_required(request.user):
        return redirect("public:home")
    if _is_courier(request.user) and order.assigned_delivery_id != request.user.id:
        return redirect("delivery:dashboard")
    items = order.items.select_related("dish")
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "start":
            if can_transition(request.user, order, Order.STATUS_ON_ROUTE):
                old_status = order.status
                order.status = Order.STATUS_ON_ROUTE
                order.save(update_fields=["status"])
                log_transition(order, request.user, old_status, order.status)
                messages.success(request, "Livraison démarrée.")
            else:
                messages.error(request, "Transition non autorisée.")
            return redirect("delivery:detail", pk=order.id)
        if action == "delivered":
            if can_transition(request.user, order, Order.STATUS_DONE):
                old_status = order.status
                order.status = Order.STATUS_DONE
                order.save(update_fields=["status"])
                log_transition(order, request.user, old_status, order.status)
                messages.success(request, "Commande marquee livree.")
            else:
                messages.error(request, "Transition non autorisée.")
            return redirect("delivery:detail", pk=order.id)
        if action == "paid":
            if order.status == Order.STATUS_CANCELLED:
                messages.error(request, "Paiement interdit : commande annulée.")
                return redirect("delivery:detail", pk=order.id)
            if order.status == Order.STATUS_PAID or order.payments.exists():
                messages.error(request, "Paiement déjà enregistré.")
                return redirect("delivery:detail", pk=order.id)
            if not can_transition(request.user, order, Order.STATUS_PAID) or order.status != Order.STATUS_DONE:
                messages.error(request, "Paiement impossible pour ce statut.")
                return redirect("delivery:detail", pk=order.id)
            session = CashSession.objects.filter(status=CashSession.STATUS_OPEN, opened_by=request.user).order_by("-opened_at").first()
            if not session:
                messages.error(request, "Caisse fermée. Ouvrez la caisse avant d'encaisser.")
                return redirect("delivery:detail", pk=order.id)
            Payment.objects.create(
                order=order,
                method=Payment.METHOD_CASH,
                amount=order.total_amount,
                session=session,
                created_by=request.user,
            )
            old_status = order.status
            order.status = Order.STATUS_PAID
            order.save(update_fields=["status"])
            log_transition(order, request.user, old_status, order.status)
            from accounts.models import AuditLog
            AuditLog.objects.create(
                action="PAYMENT",
                user=request.user,
                object_type="Order",
                object_id=str(order.id),
                new_value=f"amount={order.total_amount} method=cash",
                reason="Paiement livraison",
            )
            messages.success(request, "Paiement confirmé.")
            return redirect("delivery:detail", pk=order.id)
        if action == "issue":
            reason = request.POST.get("reason", "").strip()[:200]
            OrderStatusLog.objects.create(order=order, status=order.status, actor=request.user, reason=reason)
            messages.warning(request, "Probleme enregistre.")
            return redirect("delivery:detail", pk=order.id)
    logs = order.status_logs.all()
    return render(request, "delivery/detail.html", {"order": order, "items": items, "logs": logs})


@login_required
def assign_view(request):
    if not _is_manager(request.user):
        return redirect("public:home")
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
            if Order.objects.filter(assigned_delivery=courier, status=Order.STATUS_ON_ROUTE).exists():
                messages.error(request, "Livreur déjà en livraison.")
                return redirect("delivery:assign")
            if can_transition(request.user, order, Order.STATUS_ON_ROUTE):
                old_status = order.status
                order.assigned_delivery = courier
                order.status = Order.STATUS_ON_ROUTE
                order.save(update_fields=["assigned_delivery", "status"])
                log_transition(order, request.user, old_status, order.status, reason=f"Assigné à {courier.username}")
                messages.success(request, "Livreur attribue.")
            else:
                messages.error(request, "Transition non autorisée.")
            return redirect("delivery:deliveries")

    return render(request, "delivery/assign.html", {"orders": ready_orders, "couriers": couriers})


@login_required
def couriers_view(request):
    if not _is_manager(request.user):
        return redirect("public:home")
    couriers_qs = _courier_queryset()
    couriers = []
    for c in couriers_qs:
        active = Order.objects.filter(assigned_delivery=c, status=Order.STATUS_ON_ROUTE).exists()
        couriers.append({"user": c, "status": "busy" if active else "free"})
    return render(request, "delivery/couriers.html", {"couriers": couriers})
