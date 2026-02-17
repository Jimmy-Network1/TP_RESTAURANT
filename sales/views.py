from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import UserProfile
from .forms import OrderForm, OrderItemFormSet, PaymentForm, TableForm
from .models import Order, Payment, Table


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_SERVER, UserProfile.ROLE_CASHIER])
def tables_list(request):
    tables = Table.objects.all().order_by('name')
    return render(request, 'sales/tables_list.html', {'tables': tables})


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_SERVER])
def tables_new(request):
    if request.method == 'POST':
        form = TableForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('sales:tables')
    else:
        form = TableForm()
    return render(request, 'sales/tables_new.html', {'form': form})


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_SERVER])
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


@role_required([UserProfile.ROLE_ADMIN])
def tables_delete(request, pk):
    table = get_object_or_404(Table, pk=pk)
    if request.method == 'POST':
        table.delete()
        return redirect('sales:tables')
    return render(request, 'sales/tables_delete.html', {'table': table})


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_SERVER, UserProfile.ROLE_CASHIER, UserProfile.ROLE_DELIVERY])
def orders_list(request):
    status = request.GET.get('status')
    orders = Order.objects.select_related('table').all().order_by('-created_at')
    if status:
        orders = orders.filter(status=status)
    return render(request, 'sales/orders_list.html', {'orders': orders})


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_SERVER])
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


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_SERVER])
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


@role_required([UserProfile.ROLE_ADMIN])
def orders_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.delete()
        return redirect('sales:orders')
    return render(request, 'sales/orders_delete.html', {'order': order})


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_CASHIER])
def payments(request):
    payments = Payment.objects.select_related('order').all().order_by('-created_at')
    return render(request, 'sales/payments.html', {'payments': payments})


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_CASHIER])
def payments_new(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('sales:payments')
    else:
        form = PaymentForm()
    return render(request, 'sales/payments_new.html', {'form': form})


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_CASHIER])
def invoices(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'sales/invoices.html', {'orders': orders})
