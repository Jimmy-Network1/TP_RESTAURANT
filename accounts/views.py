from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, TemplateView

from .forms import (
    AddressForm,
    ClientProfileForm,
    LoginForm,
    RegisterForm,
    StaffCreateForm,
    ROLE_CHOICES,
)
from .models import Address, CustomerProfile

User = get_user_model()


def is_manager(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name__in=["manager", "admin"]).exists())


class LoginView(View):
    template_name = "accounts/login.html"

    def get(self, request):
        form = LoginForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data["username_or_email"]
            password = form.cleaned_data["password"]
            selected_role = form.cleaned_data.get("role")
            user = None
            if "@" in identifier:
                user_obj = User.objects.filter(email__iexact=identifier).first()
                if user_obj:
                    user = authenticate(request, username=user_obj.username, password=password)
            else:
                user = authenticate(request, username=identifier, password=password)

            if user and user.is_active:
                # Determine actual role from DB
                if user.is_superuser:
                    actual_role = "admin"
                else:
                    group = user.groups.first()
                    actual_role = group.name if group else "client"

                if selected_role != actual_role:
                    messages.error(request, "Role incorrect pour ce compte.")
                    return render(request, self.template_name, {"form": form})

                login(request, user)
                messages.success(request, "Connexion reussie.")
                return redirect("public:home")
            if user and not user.is_active:
                messages.error(request, "Compte desactive. Contactez le restaurant.")
            else:
                messages.error(request, "Email ou mot de passe incorrect.")
        return render(request, self.template_name, {"form": form})


class RegisterView(View):
    template_name = "accounts/register.html"

    def get(self, request):
        form = RegisterForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.set_password(form.cleaned_data["password1"])
                user.save()
                CustomerProfile.objects.create(user=user, phone=form.cleaned_data.get("phone", ""))
            login(request, user)
            messages.success(request, "Compte cree avec succes.")
            return redirect("public:home")
        return render(request, self.template_name, {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Vous etes deconnecte.")
    return redirect("public:home")


@method_decorator(login_required, name="dispatch")
class ProfileView(View):
    template_name = "accounts/profile.html"

    def get(self, request):
        profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
        form = ClientProfileForm(instance=profile)
        return render(request, self.template_name, {"profile": profile, "form": form})

    def post(self, request):
        profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
        form = ClientProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis a jour.")
            return redirect("accounts:profile")
        return render(request, self.template_name, {"profile": profile, "form": form})


@method_decorator(login_required, name="dispatch")
class AddressListView(View):
    template_name = "accounts/addresses.html"

    def get(self, request):
        profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
        return render(request, self.template_name, {"profile": profile, "addresses": profile.addresses.all()})


@method_decorator(login_required, name="dispatch")
class AddressCreateView(View):
    template_name = "accounts/address_form.html"

    def get(self, request):
        form = AddressForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
        form = AddressForm(request.POST)
        if form.is_valid():
            addr = form.save(commit=False)
            addr.profile = profile
            if addr.is_default:
                profile.addresses.update(is_default=False)
            addr.save()
            messages.success(request, "Adresse ajoutee.")
            return redirect("accounts:addresses")
        return render(request, self.template_name, {"form": form})


@method_decorator(login_required, name="dispatch")
class AddressUpdateView(View):
    template_name = "accounts/address_form.html"

    def get(self, request, pk):
        profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
        addr = get_object_or_404(Address, pk=pk, profile=profile)
        form = AddressForm(instance=addr)
        return render(request, self.template_name, {"form": form, "address": addr})

    def post(self, request, pk):
        profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
        addr = get_object_or_404(Address, pk=pk, profile=profile)
        form = AddressForm(request.POST, instance=addr)
        if form.is_valid():
            addr = form.save(commit=False)
            if addr.is_default:
                profile.addresses.update(is_default=False)
            addr.save()
            messages.success(request, "Adresse mise a jour.")
            return redirect("accounts:addresses")
        return render(request, self.template_name, {"form": form, "address": addr})


@method_decorator(login_required, name="dispatch")
class UsersListView(ListView):
    template_name = "accounts/users.html"
    model = User
    context_object_name = "users"
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if not is_manager(request.user):
            return HttpResponseForbidden("Acces interdit")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        role = self.request.GET.get("role")
        q = self.request.GET.get("q")
        if role == "client":
            qs = qs.filter(groups__isnull=True, is_staff=False)
        elif role:
            qs = qs.filter(groups__name=role)
        if q:
            qs = qs.filter(
                username__icontains=q
            )
        return qs.order_by("-date_joined")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = self.request.GET.get("q", "")
        ctx["role_filter"] = self.request.GET.get("role", "")
        ctx["roles"] = [r[0] for r in ROLE_CHOICES]
        return ctx


@method_decorator(login_required, name="dispatch")
class StaffCreateView(View):
    template_name = "accounts/staff_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not is_manager(request.user):
            return HttpResponseForbidden("Acces interdit")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        form = StaffCreateForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = StaffCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Utilisateur staff cree.")
            return redirect("accounts:users")
        return render(request, self.template_name, {"form": form})


@login_required
def toggle_user_active(request, pk):
    if not is_manager(request.user):
        return HttpResponseForbidden("Acces interdit")
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    messages.success(request, "Statut utilisateur mis a jour.")
    return redirect("accounts:users")


class SimplePage(TemplateView):
    pass
