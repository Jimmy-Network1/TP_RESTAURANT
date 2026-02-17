from django.shortcuts import render

from .models import KitchenTicket


def board(request):
    tickets = KitchenTicket.objects.select_related('order').all().order_by('created_at')
    return render(request, 'kitchen/board.html', {'tickets': tickets})
