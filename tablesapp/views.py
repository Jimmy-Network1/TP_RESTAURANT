from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, FormView, ListView, CreateView, UpdateView

from orders.models import Order
from .forms import TableForm, TableTransferForm
from .models import Table


class TablePlanView(ListView):
    model = Table
    template_name = "tables/plan.html"
    context_object_name = "tables"

    def get_queryset(self):
        qs = super().get_queryset()
        zone = self.request.GET.get("zone")
        status = self.request.GET.get("status")
        if zone:
            qs = qs.filter(zone=zone)
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        zones = (
            Table.objects.exclude(zone="")
            .values_list("zone", flat=True)
            .distinct()
            .order_by("zone")
        )
        for t in ctx["tables"]:
            t.next_reservation = t.reservations.filter(
                status__in=["PENDING", "CONFIRMED"],
                reservation_datetime__gte=timezone.now(),
            ).order_by("reservation_datetime").first()
        ctx["count_free"] = Table.objects.filter(status=Table.STATUS_FREE).count()
        ctx["count_occupied"] = Table.objects.filter(status=Table.STATUS_OCCUPIED).count()
        ctx["count_reserved"] = Table.objects.filter(status=Table.STATUS_RESERVED).count()
        ctx["zones"] = zones
        ctx["zone_filter"] = self.request.GET.get("zone", "")
        ctx["status_filter"] = self.request.GET.get("status", "")
        return ctx


class TableListView(ListView):
    model = Table
    template_name = "tables/list.html"
    context_object_name = "tables"

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q")
        status = self.request.GET.get("status")
        if q:
            qs = qs.filter(name__icontains=q)
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_filter"] = self.request.GET.get("status", "")
        ctx["query"] = self.request.GET.get("q", "")
        ctx["table"] = Table
        return ctx


class TableDetailView(DetailView):
    model = Table
    template_name = "tables/detail.html"
    context_object_name = "table"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        table = self.object
        active_order = (
            table.orders.filter(status__in=[
                Order.STATUS_PENDING,
                Order.STATUS_PREPARING,
                Order.STATUS_READY,
                Order.STATUS_ON_ROUTE,
            ]).order_by("-created_at").first()
        )
        history = table.orders.order_by("-created_at")[:8]
        reservation = table.reservations.order_by("-reservation_datetime").first()
        active_items = active_order.items.select_related("dish") if active_order else []
        ctx.update({
            "active_order": active_order,
            "history": history,
            "reservation": reservation,
            "active_items": active_items,
        })
        return ctx


class TableCreateView(CreateView):
    model = Table
    form_class = TableForm
    template_name = "tables/form.html"
    success_url = reverse_lazy("tables:plan")

    def form_valid(self, form):
        messages.success(self.request, "Table créée avec succès.")
        return super().form_valid(form)


class TableUpdateView(UpdateView):
    model = Table
    form_class = TableForm
    template_name = "tables/form.html"
    success_url = reverse_lazy("tables:plan")

    def form_valid(self, form):
        messages.success(self.request, "Table mise à jour.")
        return super().form_valid(form)


class TableTransferView(FormView):
    template_name = "tables/transfer.html"
    form_class = TableTransferForm
    success_url = reverse_lazy("tables:plan")

    def form_valid(self, form):
        source = form.cleaned_data["source"]
        dest = form.cleaned_data["destination"]
        action = form.cleaned_data["action"]
        with transaction.atomic():
            # Déplacer la commande active si elle existe
            order = source.orders.filter(status__in=[
                Order.STATUS_PENDING,
                Order.STATUS_PREPARING,
                Order.STATUS_READY,
                Order.STATUS_ON_ROUTE,
            ]).order_by("-created_at").first()
            if order:
                order.table = dest
                order.save(update_fields=["table"])
            # Libérer source / appliquer statut de destination
            source.status = Table.STATUS_FREE
            source.save(update_fields=["status"])
            dest.status = Table.STATUS_OCCUPIED if order else dest.status
            dest.save(update_fields=["status"])
        if action == "merge":
            messages.success(self.request, "Fusion des tables effectuée.")
        else:
            messages.success(self.request, "Transfert effectué.")
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        from_id = self.request.GET.get("from")
        if from_id:
            initial["source"] = from_id
        return initial


class TableReservationsView(ListView):
    model = Table
    template_name = "tables/reservations.html"
    context_object_name = "tables"
