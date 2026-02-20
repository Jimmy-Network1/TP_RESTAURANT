from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.views.generic import TemplateView

from accounts.models import CustomerProfile
from billing.models import Payment
from inventory.models import Ingredient
from orders.models import Order
from reservations.models import Reservation
from tablesapp.models import Table


def role_flags(user):
    if not user.is_authenticated:
        return {}
    groups = set(user.groups.values_list("name", flat=True))
    return {
        "is_manager": user.is_superuser or "manager" in groups or "admin" in groups,
        "is_server": "serveur" in groups,
        "is_cook": "cuisinier" in groups,
        "is_cashier": "caissier" in groups,
        "is_delivery": "livreur" in groups,
    }


class DashboardView(TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.now().date()
        flags = role_flags(self.request.user)

        sales_today = Payment.objects.filter(created_at__date=today).aggregate(total=Sum("amount"))["total"] or 0
        paid_today = Payment.objects.filter(created_at__date=today).count()

        ctx.update(flags)
        ctx.update({
            "sales_today": sales_today,
            "paid_today": paid_today,
            "pending_orders": Order.objects.filter(status=Order.STATUS_PENDING).count(),
            "preparing_orders": Order.objects.filter(status=Order.STATUS_PREPARING).count(),
            "ready_orders": Order.objects.filter(status=Order.STATUS_READY).count(),
            "tables_occupied": Table.objects.filter(status=Table.STATUS_OCCUPIED).count(),
            "tables_free": Table.objects.filter(status=Table.STATUS_FREE).count(),
            "tables_reserved": Table.objects.filter(status=Table.STATUS_RESERVED).count(),
            "low_stock": Ingredient.objects.filter(quantity_in_stock__lte=models.F("alert_threshold")).count(),
        })

        ctx["recent_orders"] = Order.objects.order_by("-created_at")[:8]
        ctx["deliveries"] = Order.objects.filter(order_type=Order.TYPE_DELIVERY, status=Order.STATUS_ON_ROUTE).order_by("-created_at")[:6]
        ctx["reservations_today"] = Reservation.objects.filter(
            reservation_datetime__date=today,
            status__in=[Reservation.STATUS_PENDING, Reservation.STATUS_CONFIRMED],
        ).order_by("reservation_datetime")[:6]
        ctx["to_cash"] = Order.objects.filter(status__in=[Order.STATUS_READY, Order.STATUS_SERVED]).exclude(status=Order.STATUS_PAID)[:6]

        return ctx


class ClientDashboardView(TemplateView):
    template_name = "public/client_dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        profile = None
        if user.is_authenticated:
            profile = CustomerProfile.objects.filter(user=user).first()
        orders_qs = Order.objects.none()
        if user.is_authenticated:
            orders_qs = Order.objects.filter(models.Q(customer=user) | models.Q(customer_profile=profile)).order_by("-created_at")
        last_order = orders_qs.first()
        last_res = Reservation.objects.filter(customer_profile=profile).order_by("-reservation_datetime").first() if profile else None

        ctx.update({
            "last_order": last_order,
            "last_res": last_res,
            "recent_orders": orders_qs[:5],
            "recent_reservations": Reservation.objects.filter(customer_profile=profile).order_by("-reservation_datetime")[:5] if profile else [],
            "profile": profile,
        })
        return ctx
