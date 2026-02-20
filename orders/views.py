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
from .models import Order, OrderItem, OrderStatusLog, OrderNotification


def list_view(request):
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
    qs = Order.objects.filter(status__in=[Order.STATUS_DONE, Order.STATUS_PAID, Order.STATUS_CANCELLED]).order_by("-created_at")
    return render(request, "orders/history.html", {"orders": qs})


def delivery_view(request):
    qs = Order.objects.filter(order_type=Order.TYPE_DELIVERY).order_by("-created_at")
    return render(request, "orders/delivery.html", {"orders": qs})


def detail_view(request, pk):
    order = get_object_or_404(Order, pk=pk)
    items = order.items.select_related("dish")
    logs = order.status_logs.all()
    total = sum((i.line_total for i in items), 0)
    return render(
        request,
        "orders/detail.html",
        {"order": order, "items": items, "logs": logs, "total": total},
    )


def new_view(request):
    tables = Table.objects.all()
    reservations = Reservation.objects.filter(status=Reservation.STATUS_CONFIRMED).order_by("reservation_datetime")

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                if order.order_type == Order.TYPE_DINE_IN and not order.table:
                    form.add_error("table", "Table obligatoire pour sur place.")
                    return render(request, "orders/new.html", {"form": form, "tables": tables, "reservations": reservations})
                action = request.POST.get("action")
                order.status = Order.STATUS_DRAFT if action == "draft" else Order.STATUS_PENDING
                order.created_at = timezone.now()
                order.save()
                OrderStatusLog.objects.create(
                    order=order,
                    status=order.status,
                    actor=request.user if request.user.is_authenticated else None,
                )

                res_id = request.POST.get("reservation_id")
                if res_id:
                    reservation = Reservation.objects.filter(id=res_id, status=Reservation.STATUS_CONFIRMED).first()
                    if reservation:
                        reservation.table = order.table
                        reservation.status = Reservation.STATUS_COMPLETED
                        reservation.save(update_fields=["table", "status"])
                        if order.table:
                            order.table.status = Table.STATUS_OCCUPIED
                            order.table.save(update_fields=["status"])

                messages.success(request, "Commande creee.")
                return redirect("orders:detail", pk=order.id)
    else:
        form = OrderForm(initial={"order_type": Order.TYPE_DINE_IN})

    return render(request, "orders/new.html", {"form": form, "tables": tables, "reservations": reservations})


def edit_view(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == "POST":
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            order = form.save()
            if order.status in [Order.STATUS_PENDING, Order.STATUS_PREPARING]:
                KitchenUpdate.objects.create(
                    order=order,
                    kind=KitchenUpdate.KIND_MODIFY,
                    note="Modification après envoi cuisine",
                    created_by=request.user if request.user.is_authenticated else None,
                )
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
    return render(request, "orders/edit.html", {"form": form, "order": order})


def notifications_view(request):
    notifications = OrderNotification.objects.all()[:50]
    return render(request, "orders/notifications.html", {"notifications": notifications})


def split_view(request, pk):
    order = get_object_or_404(Order, pk=pk)
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
