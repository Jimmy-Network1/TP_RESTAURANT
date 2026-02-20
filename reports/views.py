from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Count, Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from billing.models import Payment
from inventory.models import Ingredient
from menu.models import Dish
from orders.models import Order, OrderItem


def is_manager(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name__in=["manager", "admin"]).exists())


def _date_range(request):
    today = timezone.now().date()
    preset = request.GET.get("period", "today")
    if preset == "week":
        start = today - timedelta(days=today.weekday())
        end = today
    elif preset == "month":
        start = today.replace(day=1)
        end = today
    else:
        start = request.GET.get("start")
        end = request.GET.get("end")
        if start:
            start = timezone.datetime.fromisoformat(start).date()
        if end:
            end = timezone.datetime.fromisoformat(end).date()
        if not start:
            start = today
        if not end:
            end = today
    return start, end, preset


@method_decorator(login_required, name="dispatch")
class ReportsDashboardView(View):
    template_name = "reports/dashboard.html"

    def get(self, request):
        if not is_manager(request.user):
            return redirect("public:home")
        start, end, preset = _date_range(request)
        payments = Payment.objects.filter(created_at__date__gte=start, created_at__date__lte=end)
        total_sales = payments.aggregate(total=Sum("amount"))["total"] or 0
        paid_orders_count = payments.values("order").distinct().count()
        in_progress = Order.objects.exclude(status__in=[Order.STATUS_DONE, Order.STATUS_CANCELLED]).count()
        by_type = {
            "dine_in": payments.filter(order__order_type=Order.TYPE_DINE_IN).aggregate(total=Sum("amount"))["total"] or 0,
            "delivery": payments.filter(order__order_type=Order.TYPE_DELIVERY).aggregate(total=Sum("amount"))["total"] or 0,
            "takeaway": payments.filter(order__order_type=Order.TYPE_TAKEAWAY).aggregate(total=Sum("amount"))["total"] or 0,
        }
        top_item = (
            OrderItem.objects.filter(order__payments__created_at__date__gte=start, order__payments__created_at__date__lte=end)
            .values("dish__name")
            .annotate(qty=Sum("quantity"))
            .order_by("-qty")
            .first()
        )
        low_stock = Ingredient.objects.filter(quantity_in_stock__lte=models.F("alert_threshold")).count()
        late_deliveries = Order.objects.filter(status=Order.STATUS_ON_ROUTE).count()
        kitchen_pending = Order.objects.filter(status=Order.STATUS_PENDING, created_at__lte=timezone.now() - timedelta(minutes=20)).count()

        return render(request, self.template_name, {
            "start": start,
            "end": end,
            "preset": preset,
            "total_sales": total_sales,
            "paid_orders_count": paid_orders_count,
            "in_progress": in_progress,
            "by_type": by_type,
            "top_item": top_item,
            "low_stock": low_stock,
            "late_deliveries": late_deliveries,
            "kitchen_pending": kitchen_pending,
        })


@method_decorator(login_required, name="dispatch")
class DailySalesView(View):
    template_name = "reports/daily.html"

    def get(self, request):
        if not is_manager(request.user):
            return redirect("public:home")
        day = request.GET.get("date")
        if day:
            day = timezone.datetime.fromisoformat(day).date()
        else:
            day = timezone.now().date()
        payments = Payment.objects.filter(created_at__date=day)
        total = payments.aggregate(total=Sum("amount"))["total"] or 0
        orders = Order.objects.filter(payments__created_at__date=day).distinct()
        count = orders.count()
        avg = total / count if count else 0
        return render(request, self.template_name, {
            "day": day,
            "total": total,
            "count": count,
            "avg": avg,
            "orders": orders,
        })


@method_decorator(login_required, name="dispatch")
class StatsView(View):
    template_name = "reports/stats.html"

    def get(self, request):
        if not is_manager(request.user):
            return redirect("public:home")
        start, end, preset = _date_range(request)
        payments = Payment.objects.filter(created_at__date__gte=start, created_at__date__lte=end)
        revenue = payments.aggregate(total=Sum("amount"))["total"] or 0
        type_counts = Order.objects.filter(payments__created_at__date__gte=start, payments__created_at__date__lte=end).values("order_type").annotate(c=Count("id"))
        return render(request, self.template_name, {"start": start, "end": end, "preset": preset, "revenue": revenue, "type_counts": type_counts})


@method_decorator(login_required, name="dispatch")
class TopProductsView(View):
    template_name = "reports/top_products.html"

    def get(self, request):
        if not is_manager(request.user):
            return redirect("public:home")
        start, end, preset = _date_range(request)
        category = request.GET.get("category")
        items = OrderItem.objects.filter(order__payments__created_at__date__gte=start, order__payments__created_at__date__lte=end)
        if category:
            items = items.filter(dish__category__id=category)
        ranking = items.values("dish__name").annotate(qty=Sum("quantity"), total=Sum("line_total")).order_by("-qty")
        categories = Dish.objects.values("category__id", "category__name").distinct()
        return render(request, self.template_name, {"ranking": ranking, "categories": categories, "category": category, "start": start, "end": end, "preset": preset})


@method_decorator(login_required, name="dispatch")
class DeliveryReportView(View):
    template_name = "reports/delivery.html"

    def get(self, request):
        if not is_manager(request.user):
            return redirect("public:home")
        start, end, preset = _date_range(request)
        deliveries = Order.objects.filter(order_type=Order.TYPE_DELIVERY, status=Order.STATUS_DONE, payments__created_at__date__gte=start, payments__created_at__date__lte=end).distinct()
        return render(request, self.template_name, {"deliveries": deliveries, "start": start, "end": end, "preset": preset})


@method_decorator(login_required, name="dispatch")
class ExportView(View):
    template_name = "reports/export.html"

    def get(self, request):
        if not is_manager(request.user):
            return redirect("public:home")
        return render(request, self.template_name)
