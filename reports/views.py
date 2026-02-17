import csv

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from accounts.decorators import role_required
from accounts.models import UserProfile
from sales.models import Order, OrderItem, Payment

from .models import ReportSnapshot


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_CASHIER])
def dashboard(request):
    snapshots = ReportSnapshot.objects.all().order_by('-created_at')[:10]
    today = timezone.localdate()
    orders_today = Order.objects.filter(created_at__date=today)
    payments_today = Payment.objects.filter(created_at__date=today)

    total_sales = payments_today.aggregate(total=Sum('amount'))['total'] or 0
    orders_count = orders_today.count()
    total_items = OrderItem.objects.filter(order__in=orders_today).aggregate(total=Sum('quantity'))['total'] or 0

    top_dishes = (
        OrderItem.objects.values('dish__name')
        .annotate(total=Sum('quantity'))
        .order_by('-total')[:5]
    )

    context = {
        'snapshots': snapshots,
        'total_sales': total_sales,
        'orders_count': orders_count,
        'total_items': total_items,
        'top_dishes': top_dishes,
    }
    return render(request, 'reports/dashboard.html', context)


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_CASHIER])
def export_sales_csv(request):
    today = timezone.localdate()
    orders = Order.objects.filter(created_at__date=today).select_related('table')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_today.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Type', 'Statut', 'Table', 'Total', 'Créée le'])
    for order in orders:
        writer.writerow([
            order.id,
            order.get_order_type_display(),
            order.get_status_display(),
            order.table.name if order.table else '',
            order.total_amount,
            order.created_at.strftime('%Y-%m-%d %H:%M'),
        ])
    return response


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_CASHIER])
def export_payments_csv(request):
    today = timezone.localdate()
    payments = Payment.objects.filter(created_at__date=today).select_related('order')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="payments_today.csv"'
    writer = csv.writer(response)
    writer.writerow(['Commande', 'Méthode', 'Montant', 'Date'])
    for payment in payments:
        writer.writerow([
            payment.order_id,
            payment.get_method_display(),
            payment.amount,
            payment.created_at.strftime('%Y-%m-%d %H:%M'),
        ])
    return response
