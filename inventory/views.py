from django.contrib import messages
from django.db import models
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from .forms import IngredientForm, StockMovementForm
from .models import Ingredient, StockMovement


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


class IngredientCreateView(CreateView):
    model = Ingredient
    form_class = IngredientForm
    template_name = "inventory/form.html"
    success_url = reverse_lazy("inventory:stock")

    def form_valid(self, form):
        messages.success(self.request, "Article ajoute au stock.")
        return super().form_valid(form)


class IngredientUpdateView(UpdateView):
    model = Ingredient
    form_class = IngredientForm
    template_name = "inventory/form.html"
    success_url = reverse_lazy("inventory:stock")

    def form_valid(self, form):
        messages.success(self.request, "Article mis a jour.")
        return super().form_valid(form)


class StockMovementsView(ListView):
    model = StockMovement
    template_name = "inventory/movements.html"
    context_object_name = "movements"
    paginate_by = 30

    def get_queryset(self):
        qs = super().get_queryset().select_related("ingredient")
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


class StockMovementCreateView(CreateView):
    model = StockMovement
    form_class = StockMovementForm
    template_name = "inventory/movement_form.html"
    success_url = reverse_lazy("inventory:movements")

    def form_valid(self, form):
        messages.success(self.request, "Mouvement ajoute.")
        return super().form_valid(form)


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
        return ctx
