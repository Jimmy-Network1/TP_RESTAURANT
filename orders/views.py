from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from menu.models import Dish
from reservations.models import Reservation
from tablesapp.models import Table
from .forms import OrderForm
from kitchen.models import KitchenUpdate
from accounts.notifications import notify_order_status
from .models import Order, OrderItem, OrderStatusLog, OrderNotification
from accounts.models import Notification
from .utils import (
    can_transition,
    can_edit_order,
    is_manager,
    is_server,
    is_cook,
    is_cashier,
    is_delivery,
    is_staff_user,
    log_transition,
)


def list_view(request):
    if not is_staff_user(request.user):
        messages.error(request, "Accès refusé.")
        return redirect("public:home")
    qs = Order.objects.select_related("table", "customer").order_by("-created_at")
    status = request.GET.get("status", "")
    source = request.GET.get("source", "")
    otype = request.GET.get("type", "")
    q = request.GET.get("q", "")

    if status:
        qs = qs.filter(status=status)
    if source == "TABLE":
        qs = qs.filter(table__isnull=False)
    if source == "ONLINE":
        qs = qs.filter(table__isnull=True)
    if otype:
        qs = qs.filter(order_type=otype)
    if q:
        qs = qs.filter(
            Q(id__icontains=q)
            | Q(customer__username__icontains=q)
            | Q(table__name__icontains=q)
        )

    return render(
        request,
        "orders/list.html",
        {
            "orders": qs,
            "status": status,
            "source": source,
            "type_filter": otype,
            "query": q,
        },
    )


def history_view(request):
    if not is_staff_user(request.user):
        messages.error(request, "Accès refusé.")
        return redirect("public:home")
    qs = Order.objects.filter(status__in=[Order.STATUS_DONE, Order.STATUS_PAID, Order.STATUS_CANCELLED]).order_by("-created_at")
    return render(request, "orders/history.html", {"orders": qs})


def delivery_view(request):
    if not is_staff_user(request.user):
        messages.error(request, "Accès refusé.")
        return redirect("public:home")
    qs = Order.objects.filter(order_type=Order.TYPE_DELIVERY).order_by("-created_at")
    return render(request, "orders/delivery.html", {"orders": qs})


def detail_view(request, pk):
    if not is_staff_user(request.user):
        messages.error(request, "Accès refusé.")
        return redirect("public:home")
    order = get_object_or_404(Order, pk=pk)
    items = order.items.select_related("dish")
    logs = order.status_logs.all()
    total = sum((i.line_total for i in items), 0)
    return render(
        request,
        "orders/detail.html",
        {
            "order": order,
            "items": items,
            "logs": logs,
            "total": total,
            "can_cancel": is_manager(request.user) and order.status not in [Order.STATUS_PAID, Order.STATUS_CANCELLED],
            "can_serve": order.status == Order.STATUS_READY and order.order_type == Order.TYPE_DINE_IN,
        },
    )


def new_view(request):
    if not is_staff_user(request.user):
        messages.error(request, "Accès refusé.")
        return redirect("public:home")
    tables = Table.objects.filter(status=Table.STATUS_FREE)
    table_id = request.GET.get("table")
    if table_id:
        t = Table.objects.filter(id=table_id).first()
        if t and t.status != Table.STATUS_FREE:
            messages.error(request, "Cette table est déjà occupée.")
            return redirect("tables:plan")
    reservations = Reservation.objects.filter(status=Reservation.STATUS_CONFIRMED).order_by("reservation_datetime")
    dishes = Dish.objects.filter(is_active=True).order_by("name")

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                if order.order_type == Order.TYPE_DINE_IN and not order.table:
                    form.add_error("table", "Table obligatoire pour sur place.")
                    return render(request, "orders/new.html", {"form": form, "tables": tables, "reservations": reservations, "dishes": dishes})
                action = request.POST.get("action")
                order.status = Order.STATUS_DRAFT if action == "draft" else Order.STATUS_PENDING
                order.created_at = timezone.now()
                order.save()
                OrderStatusLog.objects.create(
                    order=order,
                    status=order.status,
                    actor=request.user if request.user.is_authenticated else None,
                )
                if order.status == Order.STATUS_PENDING and order.order_type == Order.TYPE_DINE_IN and order.table:
                    if order.table.status != Table.STATUS_FREE:
                        form.add_error("table", "Cette table est déjà occupée.")
                        order.delete()
                        return render(request, "orders/new.html", {"form": form, "tables": tables, "reservations": reservations, "dishes": dishes})
                    order.table.status = Table.STATUS_OCCUPIED
                    order.table.save(update_fields=["status"])

                total = 0
                for dish in dishes:
                    raw = request.POST.get(f"qty_{dish.id}", "")
                    if not raw:
                        continue
                    try:
                        qty = int(raw)
                    except ValueError:
                        qty = 0
                    if qty > 0:
                        OrderItem.objects.create(
                            order=order,
                            dish=dish,
                            quantity=qty,
                            unit_price=dish.price,
                            line_total=dish.price * qty,
                        )
                        total += dish.price * qty

                if order.status == Order.STATUS_PENDING and total == 0:
                    form.add_error(None, "Ajoutez au moins un plat avant d'envoyer en cuisine.")
                    order.delete()
                    return render(request, "orders/new.html", {"form": form, "tables": tables, "reservations": reservations, "dishes": dishes})

                order.total_amount = total
                order.save(update_fields=["total_amount"])
                notify_order_status(order, order.status)

                res_id = request.POST.get("reservation_id")
                if res_id:
                    reservation = Reservation.objects.filter(id=res_id, status=Reservation.STATUS_CONFIRMED).first()
                    if reservation:
                        reservation.table = order.table
                        reservation.status = Reservation.STATUS_COMPLETED
                        reservation.save(update_fields=["table", "status"])
                        if order.table:
                            if order.table.status != Table.STATUS_FREE:
                                form.add_error("table", "Cette table est déjà occupée.")
                                order.delete()
                                return render(request, "orders/new.html", {"form": form, "tables": tables, "reservations": reservations, "dishes": dishes})
                            order.table.status = Table.STATUS_OCCUPIED
                            order.table.save(update_fields=["status"])

                messages.success(request, "Commande creee.")
                return redirect("orders:detail", pk=order.id)
    else:
        form = OrderForm(initial={"order_type": Order.TYPE_DINE_IN})

    return render(request, "orders/new.html", {"form": form, "tables": tables, "reservations": reservations, "dishes": dishes})


def edit_view(request, pk):
    if not is_staff_user(request.user):
        messages.error(request, "Accès refusé.")
        return redirect("public:home")
    order = get_object_or_404(Order, pk=pk)
    if not can_edit_order(request.user, order):
        messages.error(request, "Modification non autorisée pour ce statut.")
        return redirect("orders:detail", pk=order.id)
    if request.method == "POST":
        form = OrderForm(request.POST, instance=order)
        if not is_manager(request.user):
            form.fields.pop("status", None)
        if form.is_valid():
            new_status = form.cleaned_data.get("status", order.status)
            cancel_reason = request.POST.get("cancel_reason", "").strip()
            if not is_manager(request.user) and order.status != Order.STATUS_DRAFT:
                if form.cleaned_data.get("order_type") != order.order_type or form.cleaned_data.get("table") != order.table:
                    messages.error(request, "Modification de type/table non autorisée après validation.")
                    return render(request, "orders/edit.html", {"form": form, "order": order})
            if new_status != order.status:
                if new_status == Order.STATUS_CANCELLED and not cancel_reason:
                    messages.error(request, "Raison d'annulation obligatoire.")
                    return render(request, "orders/edit.html", {"form": form, "order": order})
                if not can_transition(request.user, order, new_status):
                    messages.error(request, "Transition de statut non autorisée.")
                    return render(request, "orders/edit.html", {"form": form, "order": order})
            old_status = order.status
            order = form.save(commit=False)
            order.status = new_status
            order.save()
            if order.status in [Order.STATUS_PENDING, Order.STATUS_PREPARING]:
                KitchenUpdate.objects.create(
                    order=order,
                    kind=KitchenUpdate.KIND_MODIFY,
                    note="Modification après envoi cuisine",
                    created_by=request.user if request.user.is_authenticated else None,
                )
            if old_status != order.status:
                log_transition(order, request.user, old_status, order.status, reason=cancel_reason or "Modification")
            else:
                OrderStatusLog.objects.create(
                    order=order,
                    status=order.status,
                    actor=request.user if request.user.is_authenticated else None,
                    reason="Modification",
                )
            messages.success(request, "Commande mise a jour.")
            return redirect("orders:detail", pk=order.id)
    else:
        form = OrderForm(instance=order)
        if not is_manager(request.user):
            form.fields.pop("status", None)
    return render(request, "orders/edit.html", {"form": form, "order": order})


def notifications_view(request):
    if not request.user.is_authenticated:
        messages.error(request, "Accès refusé.")
        return redirect("public:home")

    qs = Notification.objects.all().order_by("-created_at")
    if is_delivery(request.user):
        qs = qs.filter(target_role=Notification.ROLE_DELIVERY)
    elif is_server(request.user):
        qs = qs.filter(target_role=Notification.ROLE_SERVER)
    elif is_cashier(request.user):
        qs = qs.filter(target_role=Notification.ROLE_CASHIER)
    elif is_cook(request.user):
        qs = qs.filter(target_role=Notification.ROLE_COOK)
    elif is_manager(request.user):
        qs = qs.filter(target_role=Notification.ROLE_MANAGER)
    else:
        qs = qs.filter(target_role=Notification.ROLE_CLIENT, user=request.user)

    notifications = list(qs[:50])
    for n in notifications:
        n.read_by.add(request.user)

    template = "orders/notifications.html" if is_staff_user(request.user) else "public/notifications.html"
    return render(request, template, {"notifications": notifications})


def split_view(request, pk):
    if not is_staff_user(request.user):
        messages.error(request, "Accès refusé.")
        return redirect("public:home")
    order = get_object_or_404(Order, pk=pk)
    if not is_manager(request.user) and order.status not in [Order.STATUS_DRAFT, Order.STATUS_PENDING]:
        messages.error(request, "Action non autorisée pour ce statut.")
        return redirect("orders:detail", pk=order.id)
    items = order.items.select_related("dish")
    if request.method == "POST":
        action = request.POST.get("action")
        target_id = request.POST.get("target_order")
        selected = request.POST.getlist("item_ids")

        if not selected:
            messages.error(request, "Selectionnez au moins un article.")
            return redirect("orders:split", pk=order.id)

        with transaction.atomic():
            if action == "merge" and target_id:
                target = get_object_or_404(Order, pk=target_id)
                OrderItem.objects.filter(id__in=selected).update(order=target)
                OrderStatusLog.objects.create(order=target, status=target.status, reason="Fusion")
                messages.success(request, "Fusion effectuee.")
                return redirect("orders:detail", pk=target.id)

            new_order = Order.objects.create(
                order_type=order.order_type,
                status=Order.STATUS_DRAFT,
                customer=order.customer,
                customer_profile=order.customer_profile,
                delivery_address=order.delivery_address,
                table=order.table,
                note="Split depuis commande #{}".format(order.id),
            )
            OrderItem.objects.filter(id__in=selected).update(order=new_order)
            OrderStatusLog.objects.create(order=new_order, status=new_order.status, reason="Split")
            messages.success(request, "Split effectue.")
            return redirect("orders:detail", pk=new_order.id)

    candidates = Order.objects.filter(table=order.table).exclude(id=order.id) if order.table else Order.objects.none()
    return render(request, "orders/split.html", {"order": order, "items": items, "candidates": candidates})


def cancel_view(request, pk):
    if not is_staff_user(request.user):
        messages.error(request, "Accès refusé.")
        return redirect("public:home")
    order = get_object_or_404(Order, pk=pk)
    if not is_manager(request.user):
        messages.error(request, "Accès refusé.")
        return redirect("orders:detail", pk=order.id)
    if order.status in [Order.STATUS_PAID, Order.STATUS_CANCELLED]:
        messages.error(request, "Annulation impossible pour ce statut.")
        return redirect("orders:detail", pk=order.id)
    if request.method == "POST":
        reason = request.POST.get("reason", "").strip()
        if not reason:
            messages.error(request, "Raison d'annulation obligatoire.")
            return render(request, "orders/cancel.html", {"order": order})
        if not can_transition(request.user, order, Order.STATUS_CANCELLED):
            messages.error(request, "Transition non autorisée.")
            return redirect("orders:detail", pk=order.id)
        old_status = order.status
        order.status = Order.STATUS_CANCELLED
        order.save(update_fields=["status"])
        log_transition(order, request.user, old_status, order.status, reason=reason)
        messages.success(request, "Commande annulée.")
        return redirect("orders:detail", pk=order.id)
    return render(request, "orders/cancel.html", {"order": order})


def serve_view(request, pk):
    if not is_staff_user(request.user):
        messages.error(request, "Accès refusé.")
        return redirect("public:home")
    order = get_object_or_404(Order, pk=pk)
    if request.method == "POST":
        if not can_transition(request.user, order, Order.STATUS_SERVED):
            messages.error(request, "Transition non autorisée.")
            return redirect("orders:detail", pk=order.id)
        old_status = order.status
        order.status = Order.STATUS_SERVED
        order.save(update_fields=["status"])
        log_transition(order, request.user, old_status, order.status, reason="Servie")
        messages.success(request, "Commande marquée servie.")
    return redirect("orders:detail", pk=order.id)
