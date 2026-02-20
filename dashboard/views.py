from django.db import models
from django.db.models import Sum
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

from accounts.models import CustomerProfile
from billing.models import Payment, CashSession
from inventory.models import Ingredient
from orders.models import Order
from reservations.models import Reservation
from tablesapp.models import Table


def _group_names(user):
    if not user.is_authenticated:
        return set()
    return {g.strip().lower() for g in user.groups.values_list("name", flat=True)}


def _has_group(groups, *names):
    if not groups:
        return False
    names_lower = {n.strip().lower() for n in names}
    return any(g in names_lower for g in groups)


def role_flags(user):
    if not user.is_authenticated:
        return {}
    groups = _group_names(user)
    return {
        "is_manager": user.is_superuser or _has_group(groups, "manager", "admin", "gerant"),
        "is_server": _has_group(groups, "serveur"),
        "is_cook": _has_group(groups, "cuisinier"),
        "is_cashier": _has_group(groups, "caissier"),
        "is_delivery": _has_group(groups, "livreur"),
    }


def _is_staff_user(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    groups = _group_names(user)
    return _has_group(groups, "gerant", "manager", "admin", "serveur", "cuisinier", "caissier", "livreur")


def _is_client_user(user):
    if not user.is_authenticated:
        return False
    if _is_staff_user(user):
        return False
    groups = _group_names(user)
    if _has_group(groups, "client"):
        return True
    return True


class RoleProtectedView(TemplateView):
    allow_staff = False
    allow_client = False

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = reverse("accounts:login")
            return redirect(f"{login_url}?next={request.path}")
        is_staff = _is_staff_user(request.user)
        is_client = _is_client_user(request.user)
        if (self.allow_staff and is_staff) or (self.allow_client and is_client):
            return super().dispatch(request, *args, **kwargs)
        messages.error(request, "Accès refusé : vous n'avez pas les droits pour cette page.")
        return redirect("public:home")


class DashboardView(RoleProtectedView):
    template_name = "dashboard/home.html"
    allow_staff = True

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
        ctx["recent_payments"] = Payment.objects.select_related("order").order_by("-created_at")[:8]
        ctx["deliveries"] = Order.objects.filter(order_type=Order.TYPE_DELIVERY, status=Order.STATUS_ON_ROUTE).order_by("-created_at")[:6]
        ctx["reservations_today"] = Reservation.objects.filter(
            reservation_datetime__date=today,
            status__in=[Reservation.STATUS_PENDING, Reservation.STATUS_CONFIRMED],
        ).order_by("reservation_datetime")[:6]
        ctx["to_cash"] = Order.objects.filter(status__in=[Order.STATUS_READY, Order.STATUS_SERVED]).exclude(status=Order.STATUS_PAID)[:6]
        ctx["ready_to_serve"] = Order.objects.filter(status=Order.STATUS_READY).order_by("-updated_at")[:8]
        ctx["pending_kitchen"] = Order.objects.filter(status=Order.STATUS_PENDING).order_by("-updated_at")[:8]
        ctx["tables"] = Table.objects.filter(active=True).order_by("name")
        cash_session = CashSession.objects.filter(status=CashSession.STATUS_OPEN).order_by("-opened_at").first()
        cash_totals = {"count": 0, "sum": 0}
        if cash_session:
            cash_totals = cash_session.payments.aggregate(count=models.Count("id"), sum=Sum("amount"))
            cash_totals["count"] = cash_totals["count"] or 0
            cash_totals["sum"] = cash_totals["sum"] or 0
        ctx["cash_session"] = cash_session
        ctx["cash_totals"] = cash_totals
        ctx["orders_total"] = Order.objects.count()
        ctx["orders_dine_in"] = Order.objects.filter(order_type=Order.TYPE_DINE_IN).count()
        ctx["orders_delivery"] = Order.objects.filter(order_type=Order.TYPE_DELIVERY).count()
        ctx["pending_reservations"] = Reservation.objects.filter(status=Reservation.STATUS_PENDING).count()
        ctx["alerts"] = [
            {
                "label": "Stock faible",
                "count": ctx["low_stock"],
                "level": "warn" if ctx["low_stock"] else "ok",
                "url": "inventory:stock",
            },
            {
                "label": "Réservations en attente",
                "count": ctx["pending_reservations"],
                "level": "warn" if ctx["pending_reservations"] else "ok",
                "url": "reservations:staff_list",
            },
            {
                "label": "Caisse fermée + commandes à encaisser",
                "count": ctx["to_cash"].count() if hasattr(ctx["to_cash"], "count") else len(ctx["to_cash"]),
                "level": "danger" if (not cash_session and (ctx["to_cash"].count() if hasattr(ctx["to_cash"], "count") else len(ctx["to_cash"]))) else "ok",
                "url": "billing:cashdesk",
            },
        ]

        return ctx


class ClientDashboardView(RoleProtectedView):
    template_name = "public/client_dashboard.html"
    allow_client = True

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        profile = None
        if user.is_authenticated:
            profile = CustomerProfile.objects.filter(user=user).first()
        orders_qs = Order.objects.none()
        if user.is_authenticated:
            orders_qs = Order.objects.filter(models.Q(customer=user) | models.Q(customer_profile=profile)).order_by("-created_at")
        active_orders = orders_qs.exclude(status__in=[Order.STATUS_DONE, Order.STATUS_PAID, Order.STATUS_CANCELLED])
        last_order = active_orders.first()
        last_res = Reservation.objects.filter(customer_profile=profile).order_by("-reservation_datetime").first() if profile else None
        default_address = None
        if profile:
            default_address = profile.addresses.filter(is_default=True).first() or profile.addresses.first()

        ctx.update({
            "last_order": last_order,
            "last_res": last_res,
            "recent_orders": orders_qs[:3],
            "recent_reservations": Reservation.objects.filter(customer_profile=profile).order_by("-reservation_datetime")[:3] if profile else [],
            "profile": profile,
            "default_address": default_address,
        })
        return ctx
