from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView

from accounts.models import CustomerProfile, AuditLog
from accounts.notifications import notify_reservation_status
from tablesapp.models import Table
from .forms import ClientReservationForm, StaffReservationUpdateForm
from .utils import available_slots
from .models import Reservation


def staff_required(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name__iexact="gerant").exists() or user.groups.filter(name__iexact="manager").exists() or user.groups.filter(name__iexact="admin").exists()


class ClientReservationCreateView(View):
    template_name = "reservations/new.html"

    def get(self, request):
        if not request.user.is_authenticated:
            messages.info(request, "Connectez-vous pour réserver une table.")
            return redirect(f"/accounts/login/?next=/reservations/new/")
        form = ClientReservationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        if not request.user.is_authenticated:
            messages.info(request, "Connectez-vous pour réserver une table.")
            return redirect(f"/accounts/login/?next=/reservations/new/")
        form = ClientReservationForm(request.POST)
        if form.is_valid():
            profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
            res = form.save(commit=False)
            res.customer_profile = profile
            res.customer_name = request.user.get_full_name() or request.user.username
            res.customer_phone = profile.phone
            # Auto-assign a free table and reserve it
            table_qs = Table.objects.filter(active=True, status=Table.STATUS_FREE).filter(
                capacity__gte=res.party_size
            )
            if res.zone:
                table_qs = table_qs.filter(zone=res.zone)
            res.table = table_qs.order_by("capacity").first()
            if not res.table:
                messages.error(request, "Aucune table disponible pour ce créneau.")
                return render(request, self.template_name, {"form": form})
            res.status = Reservation.STATUS_CONFIRMED
            res.save()
            res.table.status = Table.STATUS_RESERVED
            res.table.save(update_fields=["status"])
            notify_reservation_status(res, res.status)
            messages.success(request, "Votre demande a ete envoyee. Confirmation en attente.")
            return redirect("reservations:client_list")
        return render(request, self.template_name, {"form": form})


@method_decorator(login_required, name="dispatch")
class ClientReservationListView(ListView):
    template_name = "reservations/list.html"
    context_object_name = "reservations"

    def get_queryset(self):
        profile, _ = CustomerProfile.objects.get_or_create(user=self.request.user)
        qs = Reservation.objects.filter(customer_profile=profile).order_by("-reservation_datetime")
        scope = self.request.GET.get("scope")
        now = timezone.now()
        if scope == "upcoming":
            qs = qs.filter(reservation_datetime__gte=now)
        elif scope == "past":
            qs = qs.filter(reservation_datetime__lt=now)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["scope"] = self.request.GET.get("scope", "")
        return ctx


@method_decorator(login_required, name="dispatch")
class ClientReservationDetailView(DetailView):
    template_name = "reservations/detail.html"
    context_object_name = "reservation"

    def get_queryset(self):
        profile, _ = CustomerProfile.objects.get_or_create(user=self.request.user)
        return Reservation.objects.filter(customer_profile=profile)

    def post(self, request, pk):
        reservation = get_object_or_404(self.get_queryset(), pk=pk)
        if reservation.status in [Reservation.STATUS_PENDING, Reservation.STATUS_CONFIRMED]:
            if reservation.reservation_datetime - timezone.now() > timezone.timedelta(hours=1):
                old_status = reservation.status
                reason = request.POST.get("reason", "").strip()[:200]
                reservation.status = Reservation.STATUS_CANCELLED
                reservation.cancelled_by = request.user
                reservation.cancelled_at = timezone.now()
                reservation.cancel_reason = reason
                reservation.save(update_fields=["status", "cancelled_by", "cancelled_at", "cancel_reason"])
                notify_reservation_status(reservation, Reservation.STATUS_CANCELLED)
                if reservation.table and reservation.table.status == Table.STATUS_RESERVED:
                    reservation.table.status = Table.STATUS_FREE
                    reservation.table.save(update_fields=["status"])
                messages.success(request, "Reservation annulee.")
                AuditLog.objects.create(
                    action="RESERVATION_STATUS",
                    user=request.user,
                    object_type="Reservation",
                    object_id=str(reservation.id),
                    old_value=old_status,
                    new_value=reservation.status,
                    reason=reason or "Annulation client",
                )
            else:
                messages.error(request, "Annulation impossible a moins d'une heure.")
        return redirect("reservations:client_detail", pk=pk)


@method_decorator(login_required, name="dispatch")
class StaffReservationListView(ListView):
    template_name = "reservations/staff_list.html"
    context_object_name = "reservations"
    paginate_by = 30

    def dispatch(self, request, *args, **kwargs):
        if not staff_required(request.user):
            return redirect("public:home")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = Reservation.objects.select_related("table").order_by("-reservation_datetime")
        status = self.request.GET.get("status")
        zone = self.request.GET.get("zone")
        q = self.request.GET.get("q")
        if status:
            qs = qs.filter(status=status)
        if zone:
            qs = qs.filter(zone=zone)
        if q:
            qs = qs.filter(Q(customer_name__icontains=q) | Q(customer_phone__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_filter"] = self.request.GET.get("status", "")
        ctx["zone_filter"] = self.request.GET.get("zone", "")
        ctx["query"] = self.request.GET.get("q", "")
        ctx["tables"] = Table.objects.filter(active=True)
        return ctx


@method_decorator(login_required, name="dispatch")
class StaffReservationDetailView(View):
    template_name = "reservations/staff_detail.html"

    def dispatch(self, request, *args, **kwargs):
        if not staff_required(request.user):
            return redirect("public:home")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk)
        form = StaffReservationUpdateForm(instance=reservation)
        return render(request, self.template_name, {"reservation": reservation, "form": form})

    def post(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk)
        form = StaffReservationUpdateForm(request.POST, instance=reservation)
        if form.is_valid():
            old_status = reservation.status
            reservation = form.save(commit=False)
            if reservation.status == Reservation.STATUS_CANCELLED:
                reservation.cancelled_by = request.user
                reservation.cancelled_at = timezone.now()
                reservation.cancel_reason = request.POST.get("cancel_reason", "").strip()[:200]
            # Auto-assign table if confirmed without table
            if reservation.status == Reservation.STATUS_CONFIRMED and not reservation.table:
                table_qs = Table.objects.filter(active=True, status=Table.STATUS_FREE).filter(
                    capacity__gte=reservation.party_size
                )
                if reservation.zone:
                    table_qs = table_qs.filter(zone=reservation.zone)
                reservation.table = table_qs.order_by("capacity").first()
            reservation.save()
            if old_status != reservation.status:
                notify_reservation_status(reservation, reservation.status)
            if reservation.status == Reservation.STATUS_CONFIRMED and reservation.table:
                reservation.table.status = Table.STATUS_RESERVED
                reservation.table.save(update_fields=["status"])
            if reservation.status in [Reservation.STATUS_CANCELLED, Reservation.STATUS_COMPLETED] and reservation.table:
                # Libere la table si elle n'est pas occupée
                if reservation.table.status == Table.STATUS_RESERVED:
                    reservation.table.status = Table.STATUS_FREE
                    reservation.table.save(update_fields=["status"])
            if old_status != reservation.status:
                AuditLog.objects.create(
                    action="RESERVATION_STATUS",
                    user=request.user,
                    object_type="Reservation",
                    object_id=str(reservation.id),
                    old_value=old_status,
                    new_value=reservation.status,
                    reason="Mise à jour staff",
                )
            messages.success(request, "Reservation mise a jour.")
            return redirect("reservations:staff_detail", pk=pk)
        return render(request, self.template_name, {"reservation": reservation, "form": form})


@login_required
def reservation_checkin(request, pk):
    if not staff_required(request.user):
        return redirect("public:home")
    reservation = get_object_or_404(Reservation, pk=pk)
    if reservation.table and reservation.status in [Reservation.STATUS_CONFIRMED, Reservation.STATUS_PENDING]:
        old_status = reservation.status
        reservation.status = Reservation.STATUS_COMPLETED
        reservation.save(update_fields=["status"])
        notify_reservation_status(reservation, Reservation.STATUS_COMPLETED)
        reservation.table.status = Table.STATUS_OCCUPIED
        reservation.table.save(update_fields=["status"])
        AuditLog.objects.create(
            action="RESERVATION_STATUS",
            user=request.user,
            object_type="Reservation",
            object_id=str(reservation.id),
            old_value=old_status,
            new_value=reservation.status,
            reason="Check-in",
        )
        messages.success(request, "Client enregistré, table occupée.")
    return redirect("reservations:staff_detail", pk=pk)


def reservation_slots(request):
    date_str = request.GET.get("date")
    party_size = request.GET.get("party_size")
    zone = request.GET.get("zone") or ""
    if not date_str or not party_size:
        return JsonResponse({"slots": []})
    try:
        date_value = timezone.datetime.fromisoformat(date_str).date()
        party_size = int(party_size)
    except Exception:
        return JsonResponse({"slots": []})
    slots = available_slots(date_value, max(party_size, 1), zone=zone or None)
    return JsonResponse({"slots": slots})
