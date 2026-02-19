from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect, render

from .forms import LoginForm, RegisterForm

User = get_user_model()


def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:users_list")
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.cleaned_data["user"])
        messages.success(request, "Connexion réussie.")
        return redirect("accounts:users_list")
    return render(request, "accounts/login.html", {"form": form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:users_list")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Compte créé et connecté.")
        return redirect("accounts:users_list")
    return render(request, "accounts/register.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Déconnecté.")
    return redirect("accounts:login")


@login_required
def users_list(request):
    q = request.GET.get("q", "").strip()
    users_qs = User.objects.all().order_by("-date_joined")
    if q:
        users_qs = users_qs.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(username__icontains=q)
            | Q(email__icontains=q)
        )
    paginator = Paginator(users_qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    def role_for(u):
        if u.is_superuser:
            return "Admin"
        if u.groups.filter(name="moderateur").exists():
            return "Modérateur"
        return "Utilisateur"

    return render(
        request,
        "accounts/users_list.html",
        {"page_obj": page_obj, "q": q, "role_for": role_for},
    )
