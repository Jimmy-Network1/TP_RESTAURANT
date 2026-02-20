from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db import models
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View
from decimal import Decimal, InvalidOperation
from django.views.generic import TemplateView

from .models import CashSession, Payment
from accounts.models import AuditLog
from orders.models import Order, OrderStatusLog

ALLOW_PARTIAL_PAYMENTS = False


def _group_names(user):
    if not user.is_authenticated:
        return set()
    return {g.strip().lower() for g in user.groups.values_list("name", flat=True)}


def _is_cashier_or_manager(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    groups = _group_names(user)
    return bool(groups.intersection({"caissier", "gerant", "manager", "admin"}))


class PaymentsView(View):
    template_name = "billing/payments.html"

    def get(self, request):
        if not _is_cashier_or_manager(request.user):
            messages.error(request, "Accès refusé.")
            return redirect("public:home")
        payments = Payment.objects.select_related("order", "session").order_by("-created_at")[:100]
        return render(request, self.template_name, {"payments": payments})


class CashDeskView(View):
    template_name = "billing/cashdesk.html"

    def get(self, request):
        if not _is_cashier_or_manager(request.user):
            messages.error(request, "Accès refusé.")
            return redirect("public:home")
        session = CashSession.objects.filter(status=CashSession.STATUS_OPEN, opened_by=request.user).order_by("-opened_at").first()
        totals = {"count": 0, "sum": 0}
        if session:
            totals = session.payments.aggregate(count=models.Count("id"), sum=Sum("amount"))
            totals["count"] = totals["count"] or 0
            totals["sum"] = totals["sum"] or 0
        context = {"session": session, "totals": totals}
        return render(request, self.template_name, context)

    def post(self, request):
        if not _is_cashier_or_manager(request.user):
            messages.error(request, "Accès refusé.")
            return redirect("public:home")
        action = request.POST.get("action")
        session = CashSession.objects.filter(status=CashSession.STATUS_OPEN, opened_by=request.user).order_by("-opened_at").first()
        if action == "open":
            if session:
                messages.warning(request, "Une caisse est déjà ouverte.")
                return redirect("billing:cashdesk")
            opening_amount = request.POST.get("opening_amount") or 0
            CashSession.objects.create(
                opening_amount=opening_amount,
                opened_by=request.user,
            )
            AuditLog.objects.create(
                action="CASH_OPEN",
                user=request.user,
                object_type="CashSession",
                object_id=str(request.user.id),
                new_value=f"opening_amount={opening_amount}",
            )
            messages.success(request, "Caisse ouverte.")
            return redirect("billing:cashdesk")
        if action == "close":
            if not session:
                messages.error(request, "Aucune caisse ouverte.")
                return redirect("billing:cashdesk")
            closing_amount = request.POST.get("closing_amount") or 0
            session.closing_amount = closing_amount
            session.status = CashSession.STATUS_CLOSED
            session.closed_at = timezone.now()
            session.closed_by = request.user
            session.save()
            AuditLog.objects.create(
                action="CASH_CLOSE",
                user=request.user,
                object_type="CashSession",
                object_id=str(session.id),
                old_value=f"opening_amount={session.opening_amount}",
                new_value=f"closing_amount={closing_amount}",
            )
            totals = session.payments.aggregate(count=models.Count("id"), sum=Sum("amount"))
            totals_count = totals["count"] or 0
            totals_sum = totals["sum"] or 0
            messages.success(request, f"Caisse fermée. Paiements: {totals_count} • Total: {totals_sum} FCFA.")
            return redirect("billing:cashdesk")
        messages.error(request, "Action invalide.")
        return redirect("billing:cashdesk")


class PaymentCreateView(View):
    template_name = "billing/payment_form.html"

    def get(self, request):
        if not _is_cashier_or_manager(request.user):
            messages.error(request, "Accès refusé.")
            return redirect("public:home")
        session = CashSession.objects.filter(status=CashSession.STATUS_OPEN, opened_by=request.user).order_by("-opened_at").first()
        eligible = Order.objects.filter(
            status__in=[Order.STATUS_READY, Order.STATUS_SERVED, Order.STATUS_ON_ROUTE]
        ).order_by("-created_at")
        return render(request, self.template_name, {"session": session, "orders": eligible})

    def post(self, request):
        if not _is_cashier_or_manager(request.user):
            messages.error(request, "Accès refusé.")
            return redirect("public:home")
        session = CashSession.objects.filter(status=CashSession.STATUS_OPEN, opened_by=request.user).order_by("-opened_at").first()
        if not session:
            messages.error(request, "Caisse fermée. Ouvrez une caisse avant d'encaisser.")
            return redirect("billing:payment_new")

        order_id = request.POST.get("order_id")
        method = request.POST.get("method", Payment.METHOD_CASH)
        amount_raw = request.POST.get("amount")
        order = Order.objects.filter(id=order_id).first()
        if not order:
            messages.error(request, "Commande introuvable.")
            return redirect("billing:payment_new")

        if order.status in [Order.STATUS_CANCELLED]:
            messages.error(request, "Paiement interdit : commande annulée.")
            return redirect("billing:payment_new")
        if order.status == Order.STATUS_PAID or order.payments.exists():
            messages.error(request, "Paiement déjà enregistré.")
            return redirect("billing:payment_new")
        if order.status not in [Order.STATUS_READY, Order.STATUS_SERVED, Order.STATUS_ON_ROUTE]:
            messages.error(request, "Paiement non autorisé pour ce statut.")
            return redirect("billing:payment_new")

        try:
            amount = Decimal(str(amount_raw))
        except (TypeError, InvalidOperation):
            messages.error(request, "Montant invalide.")
            return redirect("billing:payment_new")

        total = Decimal(str(order.total_amount))
        if not ALLOW_PARTIAL_PAYMENTS and amount != total:
            messages.error(request, "Paiement partiel interdit. Montant doit être égal au total.")
            return redirect("billing:payment_new")

        with transaction.atomic():
            Payment.objects.create(
                order=order,
                session=session,
                method=method,
                amount=amount,
                created_by=request.user,
            )
            order.status = Order.STATUS_PAID
            order.save(update_fields=["status"])
            OrderStatusLog.objects.create(order=order, status=order.status, actor=request.user, reason="Paiement")
            AuditLog.objects.create(
                action="PAYMENT",
                user=request.user,
                object_type="Order",
                object_id=str(order.id),
                new_value=f"amount={amount} method={method}",
                reason="Paiement",
            )
        messages.success(request, "Paiement enregistré.")
        return redirect("billing:payments")


class SimplePage(TemplateView):
    pass
