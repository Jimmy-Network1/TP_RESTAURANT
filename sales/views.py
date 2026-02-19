from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.http import HttpResponseBadRequest
from django.contrib import messages
from django.db import models
from django.db.models import Count, Sum
from django.utils import timezone

from .forms import OrderForm, OrderItemFormSet, PaymentForm, TableForm, TableTransferForm
from .models import Order, OrderItem, Payment, Table
from menu.models import Dish
from inventory.models import Ingredient
from kitchen.models import KitchenTicket


def tables_list(request):
    zone = request.GET.get('zone', '').strip()
    tables = Table.objects.all().order_by('name')
    if zone:
        tables = tables.filter(zone__iexact=zone)

    zones = (
        Table.objects.exclude(zone="")
        .values_list('zone', flat=True)
        .distinct()
        .order_by('zone')
    )
    stats = {
        'total': tables.count(),
        'free': tables.filter(status=Table.STATUS_FREE).count(),
        'occupied': tables.filter(status=Table.STATUS_OCCUPIED).count(),
        'reserved': tables.filter(status=Table.STATUS_RESERVED).count(),
    }
    return render(
        request,
        'sales/tables_list.html',
        {
            'tables': tables,
            'zones': zones,
            'zone': zone,
            'stats': stats,
        },
    )


def table_detail(request, pk):
    table = get_object_or_404(Table, pk=pk)
    active_orders = (
        table.orders.exclude(status__in=[Order.STATUS_CLOSED, Order.STATUS_CANCELED])
        .order_by('-created_at')
        .prefetch_related('items__dish')
    )
    history = table.orders.order_by('-created_at')[:5]
    reservations = table.reservations.order_by('-reservation_datetime')[:5]
    return render(
        request,
        'sales/table_detail.html',
        {
            'table': table,
            'active_orders': active_orders,
            'history': history,
            'reservations': reservations,
        },
    )


def tables_new(request):
    if request.method == 'POST':
        form = TableForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('sales:tables')
    else:
        form = TableForm()
    return render(request, 'sales/tables_new.html', {'form': form})


def tables_edit(request, pk):
    table = get_object_or_404(Table, pk=pk)
    if request.method == 'POST':
        form = TableForm(request.POST, instance=table)
        if form.is_valid():
            form.save()
            return redirect('sales:tables')
    else:
        form = TableForm(instance=table)
    return render(request, 'sales/tables_edit.html', {'form': form, 'table': table})


def tables_delete(request, pk):
    table = get_object_or_404(Table, pk=pk)
    if request.method == 'POST':
        table.delete()
        return redirect('sales:tables')
    return render(request, 'sales/tables_delete.html', {'table': table})


def tables_transfer(request):
    form = TableTransferForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        src = form.cleaned_data['source']
        dst = form.cleaned_data['destination']
        action = form.cleaned_data['action']
        qs = Order.objects.filter(
            table=src,
            status__in=[
                Order.STATUS_DRAFT,
                Order.STATUS_SENT,
                Order.STATUS_PREPARING,
                Order.STATUS_READY,
                Order.STATUS_SERVED,
            ],
        )
        moved = qs.update(table=dst)
        if action == 'merge':
            # nothing else specific for now, same effect
            pass
        messages.success(request, f"{moved} commande(s) transférée(s) de {src.name} vers {dst.name}.")
        return redirect('sales:tables')
    return render(request, 'sales/tables_transfer.html', {'form': form})


def orders_list(request):
    status = request.GET.get('status')
    q = request.GET.get('q', '').strip()
    orders = (
        Order.objects.select_related('table', 'assigned_delivery', 'created_by')
        .prefetch_related('items__dish')
        .all()
        .order_by('-created_at')
    )
    if status:
        orders = orders.filter(status=status)
    if q:
        orders = orders.filter(
            models.Q(id__icontains=q)
            | models.Q(customer_name__icontains=q)
            | models.Q(table__name__icontains=q)
        )
    stats = {
        'total': orders.count(),
        'draft': orders.filter(status=Order.STATUS_DRAFT).count(),
        'sent': orders.filter(status=Order.STATUS_SENT).count(),
        'preparing': orders.filter(status=Order.STATUS_PREPARING).count(),
        'ready': orders.filter(status=Order.STATUS_READY).count(),
        'served': orders.filter(status=Order.STATUS_SERVED).count(),
        'closed': orders.filter(status=Order.STATUS_CLOSED).count(),
        'canceled': orders.filter(status=Order.STATUS_CANCELED).count(),
    }
    return render(
        request,
        'sales/orders_list.html',
        {'orders': orders, 'stats': stats, 'status': status, 'q': q},
    )


def orders_new(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        formset = OrderItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            order = form.save()
            formset.instance = order
            formset.save()
            return redirect('sales:orders')
    else:
        form = OrderForm()
        formset = OrderItemFormSet()
    dishes = Dish.objects.filter(is_active=True).order_by('name')
    return render(
        request,
        'sales/orders_new.html',
        {'form': form, 'formset': formset, 'dishes': dishes},
    )


def orders_edit(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        formset = OrderItemFormSet(request.POST, instance=order)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('sales:orders')
    else:
        form = OrderForm(instance=order)
        formset = OrderItemFormSet(instance=order)
    dishes = Dish.objects.filter(is_active=True).order_by('name')
    return render(
        request,
        'sales/orders_edit.html',
        {'form': form, 'formset': formset, 'order': order, 'dishes': dishes},
    )


def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related('table', 'assigned_delivery', 'created_by').prefetch_related('items__dish'),
        pk=pk,
    )
    return render(request, 'sales/order_detail.html', {'order': order})


def orders_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.delete()
        return redirect('sales:orders')
    return render(request, 'sales/orders_delete.html', {'order': order})


def payments(request):
    method = request.GET.get('method', '')
    payments = Payment.objects.select_related('order').all().order_by('-created_at')
    if method:
        payments = payments.filter(method=method)
    total = payments.aggregate(total=Sum('amount'))['total'] or 0
    methods_totals = payments.values('method').annotate(total=Sum('amount'))
    return render(
        request,
        'sales/payments.html',
        {'payments': payments, 'method': method, 'total': total, 'methods_totals': methods_totals},
    )


def payments_new(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('sales:payments')
    else:
        form = PaymentForm()
    return render(request, 'sales/payments_new.html', {'form': form})


def payment_collect(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        form.fields['order'].queryset = Order.objects.filter(pk=order_id)
        if form.is_valid():
            form.save()
            order.status = Order.STATUS_CLOSED
            order.save(update_fields=['status', 'updated_at'])
            messages.success(request, "Paiement enregistré.")
            return redirect('sales:orders')
    else:
        form = PaymentForm(initial={'order': order})
        form.fields['order'].queryset = Order.objects.filter(pk=order_id)
    return render(request, 'sales/payment_collect.html', {'form': form, 'order': order})


def cashdesk(request):
    today = timezone.localdate()
    todays_payments = Payment.objects.filter(created_at__date=today)
    total = todays_payments.aggregate(total=Sum('amount'))['total'] or 0
    counts = todays_payments.count()
    by_method = todays_payments.values('method').annotate(total=Sum('amount'), count=Count('id'))
    return render(
        request,
        'sales/cashdesk.html',
        {'total': total, 'counts': counts, 'by_method': by_method, 'today': today},
    )


def invoices(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'sales/invoices.html', {'orders': orders})


def invoice_detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related('items__dish', 'payments'), pk=pk)
    return render(request, 'sales/invoice_detail.html', {'order': order})


def dashboard(request):
    metrics = {
        'sales_today': Payment.objects.filter(created_at__date=timezone.localdate()).aggregate(total=Sum('amount'))[
            'total'
        ]
        or 0,
        'orders_active': Order.objects.exclude(status__in=[Order.STATUS_CLOSED, Order.STATUS_CANCELED]).count(),
        'kitchen_pending': KitchenTicket.objects.filter(status=KitchenTicket.STATUS_PENDING).count(),
        'tables_busy': Table.objects.filter(status=Table.STATUS_OCCUPIED).count(),
        'tables_total': Table.objects.count(),
    }
    notifications = [
        {'title': 'Commandes prêtes', 'time': 'il y a 2 min', 'message': '2 tickets marqués prêts en cuisine.'},
        {'title': 'Stock faible', 'time': 'il y a 15 min', 'message': '3 ingrédients sous le seuil.'},
    ]
    mini = {
        'top_product': 'Burger bœuf braisé',
        'revenue': metrics['sales_today'],
        'trend': 'En hausse',
        'trend_percent': 64,
    }
    recent_orders = (
        Order.objects.select_related('table')
        .order_by('-created_at')
        .prefetch_related('items')[:8]
    )
    recent_payments = Payment.objects.select_related('order').order_by('-created_at')[:8]
    return render(
        request,
        'staff/dashboard.html',
        {
            'metrics': metrics,
            'notifications': notifications,
            'mini': mini,
            'recent_orders': recent_orders,
            'recent_payments': recent_payments,
        },
    )


def order_status(request, pk, status):
    """Met à jour le statut d'une commande depuis un bouton rapide."""
    order = get_object_or_404(Order, pk=pk)
    valid_statuses = {choice[0] for choice in Order.STATUS_CHOICES}

    if status not in valid_statuses:
        return HttpResponseBadRequest("Statut invalide")

    if request.method == 'POST':
        order.status = status
        order.save(update_fields=['status', 'updated_at'])
    # Redirige vers la page précédente si disponible, sinon vers la liste.
    return redirect(request.META.get('HTTP_REFERER') or reverse('sales:orders'))
