from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db import models
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView
from django.shortcuts import redirect

from .forms import IngredientForm, StockMovementForm
from .models import Ingredient, StockMovement, InventoryAlert
from accounts.models import AuditLog

def _group_names(user):
    if not user.is_authenticated:
        return set()
    return {g.strip().lower() for g in user.groups.values_list("name", flat=True)}


def _is_stock_manager(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return bool(_group_names(user).intersection({"gerant", "manager", "admin"}))


def _is_stock_operator(user):
    if not user.is_authenticated:
        return False
    if _is_stock_manager(user):
        return True
    return False


class StockListView(ListView):
    model = Ingredient
    template_name = "inventory/stock.html"
    context_object_name = "items"
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(name__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = self.request.GET.get("q", "")
        ctx["ingredient"] = Ingredient
        return ctx
    
    def dispatch(self, request, *args, **kwargs):
        if not _is_stock_operator(request.user):
            messages.error(request, "Accès stock refusé.")
            return redirect("public:home")
        return super().dispatch(request, *args, **kwargs)


class IngredientCreateView(CreateView):
    model = Ingredient
    form_class = IngredientForm
    template_name = "inventory/form.html"
    success_url = reverse_lazy("inventory:stock")

    def form_valid(self, form):
        if not _is_stock_manager(self.request.user):
            messages.error(self.request, "Action réservée au gérant.")
            return redirect("inventory:stock")
        response = super().form_valid(form)
        qty = form.instance.quantity_in_stock or 0
        if qty > 0:
            StockMovement.objects.create(
                ingredient=form.instance,
                movement_type=StockMovement.TYPE_IN,
                quantity=qty,
                note="Stock initial",
                created_by=self.request.user,
            )
        messages.success(self.request, "Article ajoute au stock.")
        return response

    def dispatch(self, request, *args, **kwargs):
        if not _is_stock_manager(request.user):
            messages.error(request, "Action réservée au gérant.")
            return redirect("inventory:stock")
        return super().dispatch(request, *args, **kwargs)


class IngredientUpdateView(UpdateView):
    model = Ingredient
    form_class = IngredientForm
    template_name = "inventory/form.html"
    success_url = reverse_lazy("inventory:stock")

    def form_valid(self, form):
        if not _is_stock_manager(self.request.user):
            messages.error(self.request, "Action réservée au gérant.")
            return redirect("inventory:stock")
        messages.success(self.request, "Article mis a jour.")
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Interdit de modifier directement la quantité sans mouvement
        form.fields.pop("quantity_in_stock", None)
        return form

    def dispatch(self, request, *args, **kwargs):
        if not _is_stock_manager(request.user):
            messages.error(request, "Action réservée au gérant.")
            return redirect("inventory:stock")
        return super().dispatch(request, *args, **kwargs)


class StockMovementsView(ListView):
    model = StockMovement
    template_name = "inventory/movements.html"
    context_object_name = "movements"
    paginate_by = 30

    def get_queryset(self):
        qs = super().get_queryset().select_related("ingredient", "created_by")
        start = self.request.GET.get("start")
        end = self.request.GET.get("end")
        if start:
            qs = qs.filter(created_at__date__gte=start)
        if end:
            qs = qs.filter(created_at__date__lte=end)
        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["start"] = self.request.GET.get("start", "")
        ctx["end"] = self.request.GET.get("end", "")
        return ctx
    
    def dispatch(self, request, *args, **kwargs):
        if not _is_stock_operator(request.user):
            messages.error(request, "Accès stock refusé.")
            return redirect("public:home")
        return super().dispatch(request, *args, **kwargs)


class StockMovementCreateView(CreateView):
    model = StockMovement
    form_class = StockMovementForm
    template_name = "inventory/movement_form.html"
    success_url = reverse_lazy("inventory:movements")

    def form_valid(self, form):
        if not _is_stock_operator(self.request.user):
            messages.error(self.request, "Accès refusé.")
            return redirect("inventory:movements")
        if form.cleaned_data.get("movement_type") == StockMovement.TYPE_ADJUST and not _is_stock_manager(self.request.user):
            messages.error(self.request, "Ajustement réservé au gérant.")
            return redirect("inventory:movements")
        ingredient = form.cleaned_data["ingredient"]
        qty = form.cleaned_data["quantity"]
        mtype = form.cleaned_data["movement_type"]
        old_qty = ingredient.quantity_in_stock
        new_qty = ingredient.quantity_in_stock
        if mtype == StockMovement.TYPE_IN:
            new_qty = ingredient.quantity_in_stock + qty
        elif mtype == StockMovement.TYPE_OUT:
            new_qty = ingredient.quantity_in_stock - qty
        elif mtype == StockMovement.TYPE_ADJUST:
            new_qty = ingredient.quantity_in_stock + qty
        if new_qty < 0:
            messages.error(self.request, "Stock négatif interdit.")
            return redirect("inventory:movement_new")
        with transaction.atomic():
            movement = form.save(commit=False)
            movement.created_by = self.request.user
            movement.save()
            ingredient.quantity_in_stock = new_qty
            ingredient.save(update_fields=["quantity_in_stock"])
            if ingredient.alert_threshold and ingredient.alert_threshold > 0:
                if old_qty > ingredient.alert_threshold and new_qty <= ingredient.alert_threshold:
                    InventoryAlert.objects.create(
                        ingredient=ingredient,
                        message=f"Stock faible: {ingredient.name} ({new_qty} {ingredient.get_unit_display()})",
                        created_by=self.request.user,
                    )
            AuditLog.objects.create(
                action="STOCK_MOVE",
                user=self.request.user,
                object_type="Ingredient",
                object_id=str(ingredient.id),
                old_value=f"qty={old_qty}",
                new_value=f"qty={new_qty}",
                reason=movement.note,
            )
        messages.success(self.request, "Mouvement ajoute.")
        return redirect(self.success_url)

    def dispatch(self, request, *args, **kwargs):
        if not _is_stock_operator(request.user):
            messages.error(request, "Accès refusé.")
            return redirect("inventory:movements")
        return super().dispatch(request, *args, **kwargs)


class StockAlertsView(ListView):
    model = Ingredient
    template_name = "inventory/alerts.html"
    context_object_name = "items"

    def get_queryset(self):
        return Ingredient.objects.filter(quantity_in_stock__lte=models.F("alert_threshold"))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        percent_map = {}
        for item in ctx["items"]:
            if item.alert_threshold and item.alert_threshold > 0:
                percent = float(item.quantity_in_stock) / float(item.alert_threshold) * 100
                percent_map[item.id] = min(100, max(0, round(percent)))
            else:
                percent_map[item.id] = 0
        ctx["percent_map"] = percent_map
        ctx["alerts"] = InventoryAlert.objects.select_related("ingredient", "created_by")[:10]
        return ctx

    def dispatch(self, request, *args, **kwargs):
        if not _is_stock_operator(request.user):
            messages.error(request, "Accès stock refusé.")
            return redirect("public:home")
        return super().dispatch(request, *args, **kwargs)
