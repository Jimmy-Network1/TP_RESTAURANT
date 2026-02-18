from django.shortcuts import get_object_or_404, redirect, render

from .forms import ReservationForm
from .models import Reservation


def list_view(request):
    reservations = Reservation.objects.select_related('table').all().order_by('-reservation_datetime')
    return render(request, 'reservations/list.html', {'reservations': reservations})


def reservation_new(request):
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('reservations:list')
    else:
        form = ReservationForm()
    return render(request, 'reservations/new.html', {'form': form})


def reservation_edit(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        # mise à jour rapide du statut si fourni
        status = request.POST.get('status')
        if status:
            reservation.status = status
            reservation.save(update_fields=['status'])
            return redirect('reservations:list')
        form = ReservationForm(request.POST, instance=reservation)
        if form.is_valid():
            form.save()
            return redirect('reservations:list')
    else:
        form = ReservationForm(instance=reservation)
    return render(request, 'reservations/edit.html', {'form': form, 'reservation': reservation})


def reservation_delete(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        reservation.delete()
        return redirect('reservations:list')
    return render(request, 'reservations/delete.html', {'reservation': reservation})
