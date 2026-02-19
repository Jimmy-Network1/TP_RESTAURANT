from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.urls import reverse
from django.contrib import messages

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


def bar_board(request):
    """Vue simplifiée pour le bar : filtre station 'Bar' si elle existe."""
    tickets = (
        KitchenTicket.objects.select_related('order', 'station')
        .prefetch_related('items__dish')
        .filter(station__name__icontains='bar')
        .order_by('created_at')
    )
    context = {'tickets': tickets}
    return render(request, 'kitchen/bar.html', context)


def ticket_detail(request, pk):
    ticket = get_object_or_404(
        KitchenTicket.objects.select_related('order', 'station').prefetch_related('items__dish'),
        pk=pk,
    )
    return render(request, 'kitchen/ticket_detail.html', {'ticket': ticket})


def ticket_status(request, pk, status):
    ticket = get_object_or_404(KitchenTicket, pk=pk)
    valid = {choice[0] for choice in KitchenTicket.STATUS_CHOICES}
    if status not in valid:
        messages.error(request, "Statut invalide")
        return redirect(request.META.get('HTTP_REFERER') or reverse('kitchen:board'))

    if request.method == 'POST':
        ticket.status = status
        if status == KitchenTicket.STATUS_PREPARING and not ticket.started_at:
            ticket.started_at = timezone.now()
        if status == KitchenTicket.STATUS_READY:
            ticket.ready_at = timezone.now()
        ticket.save(update_fields=['status', 'started_at', 'ready_at'])
        messages.success(request, f"Ticket #{ticket.id} mis à jour.")
    return redirect(request.META.get('HTTP_REFERER') or reverse('kitchen:board'))
