from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.shortcuts import redirect, render
from django.urls import reverse
from sales.models import Order
from reservations.models import Reservation

ROLES = ["gerant", "serveur", "coursier", "client"]


def _ensure_groups():
    for role in ROLES:
        Group.objects.get_or_create(name=role)


def login_view(request):
    _ensure_groups()
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        role = request.POST.get('role', '')
        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "Mauvais identifiants.")
            return render(request, 'accounts/login.html')
        if role not in ROLES:
            messages.error(request, "Rôle non autorisé.")
            return render(request, 'accounts/login.html')
        # Vérifie l'appartenance au groupe sélectionné
        if not user.groups.filter(name=role).exists():
            messages.error(request, "Mauvais rôle sélectionné pour cet utilisateur.")
            return render(request, 'accounts/login.html')
        login(request, user)
        # Redirection selon rôle
        if role == 'gerant':
            return redirect('reports:dashboard')
        if role == 'serveur':
            return redirect('sales:orders')
        if role == 'coursier':
            return redirect('sales:orders')
        return redirect('public:home')
    return render(request, 'auth/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "Déconnecté.")
    return redirect('public:home')


def roles_view(request):
    return render(request, 'accounts/roles.html')


def register_view(request):
    _ensure_groups()
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        role = 'client'  # seul client autorisé en self-signup

        if not all([full_name, username, email, password1, password2]):
            messages.error(request, "Tous les champs obligatoires doivent être remplis.")
            return render(request, 'accounts/register.html')
        if password1 != password2:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, 'accounts/register.html')
        if len(password1) < 8 or not any(c.isupper() for c in password1) or not any(c.isdigit() for c in password1):
            messages.error(request, "Mot de passe trop faible (8+, 1 majuscule, 1 chiffre).")
            return render(request, 'accounts/register.html')
        if User.objects.filter(username=username).exists():
            messages.error(request, "Nom d'utilisateur déjà pris.")
            return render(request, 'accounts/register.html')
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email déjà utilisé.")
            return render(request, 'accounts/register.html')

        user = User.objects.create_user(username=username, email=email, password=password1)
        user.first_name = full_name
        user.save()
        group = Group.objects.get(name=role)
        user.groups.add(group)
        login(request, user)
        messages.success(request, "Compte créé avec succès.")
        return redirect('public:home')

    return render(request, 'auth/register.html')


@login_required
def profile_view(request):
    groups = list(request.user.groups.values_list('name', flat=True))
    role = groups[0] if groups else "membre"
    cart_count = request.session.get('cart_count', 0)
    recent_orders = Order.objects.filter(
        created_by=request.user
    ).order_by('-created_at')[:5]
    recent_reservations = Reservation.objects.filter(
        customer_name=request.user.get_full_name() or request.user.username
    ).order_by('-reservation_datetime')[:5]
    return render(
        request,
        'accounts/profile.html',
        {
            'user': request.user,
            'groups': groups,
            'role': role,
            'cart_count': cart_count,
            'recent_orders': recent_orders,
            'recent_reservations': recent_reservations,
        },
    )
