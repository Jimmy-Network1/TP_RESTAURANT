from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render

from .models import UserProfile


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
        messages.error(request, "Identifiants invalides.")
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return render(request, 'accounts/logout.html')


@login_required
def roles_view(request):
    profiles = UserProfile.objects.select_related('user').all().order_by('user__username')
    return render(request, 'accounts/roles.html', {'profiles': profiles})
