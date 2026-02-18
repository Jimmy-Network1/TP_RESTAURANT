from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.http import HttpResponseBadRequest

from .forms import OrderForm, OrderItemFormSet, PaymentForm, TableForm
from .models import Order, OrderItem, Payment, Table


def tables_list(request):
    tables = Table.objects.all().order_by('name')
    return render(request, 'sales/tables_list.html', {'tables': tables})


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


def orders_list(request):
    status = request.GET.get('status')
    orders = (
        Order.objects.select_related('table', 'assigned_delivery', 'created_by')
        .prefetch_related('items__dish')
        .all()
        .order_by('-created_at')
    )
    if status:
        orders = orders.filter(status=status)
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
    return render(request, 'sales/orders_list.html', {'orders': orders, 'stats': stats, 'status': status})


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
    return render(request, 'sales/orders_new.html', {'form': form, 'formset': formset})


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
    return render(request, 'sales/orders_edit.html', {'form': form, 'formset': formset, 'order': order})


def orders_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.delete()
        return redirect('sales:orders')
    return render(request, 'sales/orders_delete.html', {'order': order})


def payments(request):
    payments = Payment.objects.select_related('order').all().order_by('-created_at')
    return render(request, 'sales/payments.html', {'payments': payments})


def payments_new(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('sales:payments')
    else:
        form = PaymentForm()
    return render(request, 'sales/payments_new.html', {'form': form})


def invoices(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'sales/invoices.html', {'orders': orders})


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
