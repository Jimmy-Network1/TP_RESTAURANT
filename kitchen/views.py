from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView

from orders.models import Order, OrderNotification
from accounts.notifications import create_notification
from orders.utils import can_transition, log_transition


def kitchen_required(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if user.groups.filter(name__iexact="gerant").exists():
        return True
    if user.groups.filter(name__iexact="manager").exists():
        return True
    return user.groups.filter(name__iexact="cuisinier").exists()


@method_decorator(login_required, name="dispatch")
class KitchenBoardView(ListView):
    template_name = "kitchen/board.html"
    context_object_name = "orders"

    def dispatch(self, request, *args, **kwargs):
        if not kitchen_required(request.user):
            return redirect("public:home")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = Order.objects.filter(status__in=[
            Order.STATUS_PENDING,
            Order.STATUS_PREPARING,
            Order.STATUS_READY,
        ]).order_by("created_at")
        status = self.request.GET.get("status")
        source = self.request.GET.get("source")
        otype = self.request.GET.get("type")
        if status in [Order.STATUS_PENDING, Order.STATUS_PREPARING, Order.STATUS_READY]:
            qs = qs.filter(status=status)
        if source == "TABLE":
            qs = qs.filter(order_type=Order.TYPE_DINE_IN)
        if source == "ONLINE":
            qs = qs.filter(order_type__in=[Order.TYPE_DELIVERY, Order.TYPE_TAKEAWAY])
        if otype:
            qs = qs.filter(order_type=otype)
        return qs.select_related("table").prefetch_related("items", "items__dish", "kitchen_updates")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["count_pending"] = Order.objects.filter(status=Order.STATUS_PENDING).count()
        ctx["count_preparing"] = Order.objects.filter(status=Order.STATUS_PREPARING).count()
        ctx["count_ready"] = Order.objects.filter(status=Order.STATUS_READY).count()
        ctx["status_filter"] = self.request.GET.get("status", "")
        ctx["source_filter"] = self.request.GET.get("source", "")
        ctx["type_filter"] = self.request.GET.get("type", "")
        ctx["now"] = timezone.now()
        orders = list(self.object_list)
        kitchen_orders = []
        bar_orders = []
        count_server = 0
        count_courier = 0
        for o in orders:
            has_drink = False
            has_food = False
            if o.order_type == Order.TYPE_DELIVERY:
                count_courier += 1
            else:
                count_server += 1
            for it in o.items.all():
                cat = (it.dish.category.name or "").lower()
                if "boisson" in cat:
                    has_drink = True
                else:
                    has_food = True
            if has_food:
                kitchen_orders.append(o)
            if has_drink:
                bar_orders.append(o)
        ctx["kitchen_orders"] = kitchen_orders
        ctx["bar_orders"] = bar_orders
        ctx["count_server"] = count_server
        ctx["count_courier"] = count_courier
        ctx["latest_ticket_id"] = Order.objects.filter(status__in=[Order.STATUS_PENDING, Order.STATUS_PREPARING]).order_by("-created_at").values_list("id", flat=True).first() or 0
        return ctx


@method_decorator(login_required, name="dispatch")
class KitchenTicketView(DetailView):
    template_name = "kitchen/ticket.html"
    model = Order
    context_object_name = "order"

    def dispatch(self, request, *args, **kwargs):
        if not kitchen_required(request.user):
            return redirect("public:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["items"] = self.object.items.select_related("dish", "dish__category")
        ctx["updates"] = self.object.kitchen_updates.order_by("-created_at")
        return ctx


@login_required
def kitchen_action(request, pk):
    if not kitchen_required(request.user):
        return redirect("public:home")
    order = get_object_or_404(Order, pk=pk)
    action = request.POST.get("action")
    if action == "start":
        if can_transition(request.user, order, Order.STATUS_PREPARING):
            old_status = order.status
            order.status = Order.STATUS_PREPARING
            order.save(update_fields=["status"])
            log_transition(order, request.user, old_status, order.status)
            messages.success(request, "Commande en préparation.")
        else:
            messages.error(request, "Transition non autorisée.")
    elif action == "ready":
        if can_transition(request.user, order, Order.STATUS_READY):
            old_status = order.status
            order.status = Order.STATUS_READY
            order.save(update_fields=["status"])
            log_transition(order, request.user, old_status, order.status)
            if order.order_type == Order.TYPE_DELIVERY:
                OrderNotification.objects.create(
                    order=order,
                    target=OrderNotification.TARGET_DELIVERY,
                    message=f"Commande #{order.id} prête pour {order.get_order_type_display()}",
                )
                create_notification(
                    target_role="delivery",
                    message=f"Commande #{order.id} prête à livrer",
                    url=f"/orders/{order.id}/",
                )
                messages.success(request, "Commande prête. Livraison notifiée.")
            else:
                OrderNotification.objects.create(
                    order=order,
                    target=OrderNotification.TARGET_SERVER,
                    message=f"Commande #{order.id} prête pour table {order.table.name if order.table else '-'}",
                )
                create_notification(
                    target_role="server",
                    message=f"Commande #{order.id} prête à servir",
                    url=f"/orders/{order.id}/",
                )
                messages.success(request, "Commande prête. Serveur notifié.")
        else:
            messages.error(request, "Transition non autorisée.")
    elif action == "issue":
        note = request.POST.get("note", "")[:200]
        order.kitchen_issue = True
        order.kitchen_issue_note = note
        order.save(update_fields=["kitchen_issue", "kitchen_issue_note"])
        messages.error(request, "Problème signalé.")
    referer = request.META.get("HTTP_REFERER")
    return redirect(referer) if referer else redirect("kitchen:board")


@method_decorator(login_required, name="dispatch")
class KitchenBarView(ListView):
    template_name = "kitchen/bar.html"
    context_object_name = "orders"

    def dispatch(self, request, *args, **kwargs):
        if not kitchen_required(request.user):
            return redirect("public:home")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Order.objects.filter(status__in=[
            Order.STATUS_PENDING,
            Order.STATUS_PREPARING,
            Order.STATUS_READY,
        ], items__dish__category__name__icontains="boisson").distinct()


@method_decorator(login_required, name="dispatch")
class KitchenHistoryView(ListView):
    template_name = "kitchen/history.html"
    context_object_name = "orders"

    def dispatch(self, request, *args, **kwargs):
        if not kitchen_required(request.user):
            return redirect("public:home")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Order.objects.filter(status=Order.STATUS_READY).order_by("-created_at")
