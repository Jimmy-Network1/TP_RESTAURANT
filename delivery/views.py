from collections import defaultdict

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from sales.models import Order

User = get_user_model()


def clients_list(request):
    q = request.GET.get('q', '').strip()
    customers = (
        Order.objects.filter(order_type=Order.TYPE_DELIVERY)
        .values('customer_name', 'customer_phone', 'delivery_address')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    if q:
        customers = customers.filter(
            Q(customer_name__icontains=q)
            | Q(customer_phone__icontains=q)
            | Q(delivery_address__icontains=q)
        )
    return render(request, 'delivery/clients_list.html', {'customers': customers, 'q': q})


def client_detail(request, phone):
    orders = (
        Order.objects.filter(customer_phone=phone, order_type=Order.TYPE_DELIVERY)
        .order_by('-created_at')
        .select_related('assigned_delivery')
    )
    customer = orders.first()
    return render(request, 'delivery/client_detail.html', {'orders': orders, 'customer': customer, 'phone': phone})


def deliveries_list(request):
    status = request.GET.get('status', '')
    deliveries = (
        Order.objects.filter(order_type=Order.TYPE_DELIVERY)
        .select_related('assigned_delivery')
        .order_by('-created_at')
    )
    if status:
        deliveries = deliveries.filter(status=status)
    return render(request, 'delivery/deliveries_list.html', {'deliveries': deliveries, 'status': status})


def couriers_list(request):
    couriers = User.objects.filter(groups__name__iexact='coursier').order_by('username')
    return render(request, 'delivery/couriers_list.html', {'couriers': couriers})


def assign(request):
    couriers = User.objects.filter(groups__name__iexact='coursier').order_by('username')
    pending = Order.objects.filter(order_type=Order.TYPE_DELIVERY).exclude(status=Order.STATUS_CLOSED).order_by(
        '-created_at'
    )
    if request.method == 'POST':
        courier_id = request.POST.get('courier')
        order_id = request.POST.get('order')
        courier = get_object_or_404(User, pk=courier_id)
        order = get_object_or_404(Order, pk=order_id)
        order.assigned_delivery = courier
        order.save(update_fields=['assigned_delivery'])
        messages.success(request, f"Commande #{order.id} assignée à {courier.username}.")
        return redirect('delivery:deliveries')
    return render(request, 'delivery/assign.html', {'couriers': couriers, 'orders': pending})
