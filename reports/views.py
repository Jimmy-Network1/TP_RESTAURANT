from django.shortcuts import render

from .models import ReportSnapshot


def dashboard(request):
    snapshots = ReportSnapshot.objects.all().order_by('-created_at')[:10]
    def pick(data, *keys, default=None):
        for k in keys:
            if k in data:
                return data[k]
        return default

    def normalize(snapshot: ReportSnapshot):
        data = snapshot.data or {}
        return {
            'id': snapshot.id,
            'period': snapshot.get_period_type_display(),
            'start': snapshot.period_start,
            'end': snapshot.period_end,
            'created_at': snapshot.created_at,
            'ca': pick(data, 'turnover', 'ca', 'ca_total', 'revenue', 'chiffre_affaires', default=0),
            'orders': pick(data, 'orders', 'commandes', 'orders_count', default=0),
            'avg_ticket': pick(data, 'avg_ticket', 'ticket_moyen', 'average_ticket', default=0),
            'top_dish': pick(data, 'top_dish', 'best_seller', 'top_plate', default=""),
        }

    normalized = [normalize(s) for s in snapshots]
    last = normalized[0] if normalized else None
    total_ca = last['ca'] if last else 0
    orders = last['orders'] if last else 0
    avg_ticket = last['avg_ticket'] if last else 0
    top_dish = last['top_dish'] if last else ""

    context = {
        'snapshots': snapshots,
        'rows': normalized,
        'total_ca': total_ca,
        'orders': orders,
        'avg_ticket': avg_ticket,
        'top_dish': top_dish,
        'snapshots_count': snapshots.count(),
        'last_snapshot': snapshots[0] if snapshots else None,
    }
    return render(request, 'reports/dashboard.html', context)
