from django.shortcuts import render

from .models import KitchenTicket


def board(request):
    tickets = (
        KitchenTicket.objects.select_related('order')
        .prefetch_related('items__dish')
        .all()
        .order_by('created_at')
    )

    pending = [t for t in tickets if t.status == KitchenTicket.STATUS_PENDING]
    preparing = [t for t in tickets if t.status == KitchenTicket.STATUS_PREPARING]
    ready = [t for t in tickets if t.status == KitchenTicket.STATUS_READY]

    stats = {
        'total': len(tickets),
        'pending': len(pending),
        'preparing': len(preparing),
        'ready': len(ready),
    }

    context = {
        'tickets': tickets,
        'pending': pending,
        'preparing': preparing,
        'ready': ready,
        'stats': stats,
    }
    return render(request, 'kitchen/board.html', context)
