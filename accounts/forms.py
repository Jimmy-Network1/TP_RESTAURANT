from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import Group

from .models import CustomerProfile, Address

User = get_user_model()

ROLE_CHOICES = (
    ("client", "Client"),
    ("serveur", "Serveur"),
    ("cuisinier", "Cuisinier"),
    ("caissier", "Caissier"),
    ("livreur", "Livreur"),
    ("gerant", "Gerant"),
)


class LoginForm(forms.Form):
    username_or_email = forms.CharField(
        label="Nom d'utilisateur ou Email",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nom d'utilisateur ou email"}),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Mot de passe"}),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.Select(attrs={"class": "form-control"}))


class RegisterForm(forms.ModelForm):
    phone = forms.CharField(label="Téléphone", widget=forms.TextInput(attrs={"class": "form-control"}))
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        validators=[validate_password],
    )
    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Cet email est deja utilise.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if username and User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est deja pris.")
        return username

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            self.add_error("password2", "Les mots de passe ne correspondent pas.")
        return cleaned


class ClientProfileForm(forms.ModelForm):
    class Meta:
        model = CustomerProfile
        fields = ["phone", "preferences"]
        widgets = {
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "preferences": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ["label", "city", "district", "details", "is_default"]
        widgets = {
            "label": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "district": forms.TextInput(attrs={"class": "form-control"}),
            "details": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "is_default": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class StaffCreateForm(forms.ModelForm):
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.Select(attrs={"class": "form-control"}))
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        validators=[validate_password],
    )
    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    is_active = forms.BooleanField(required=False, initial=True)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            self.add_error("password2", "Les mots de passe ne correspondent pas.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_staff = True
        user.is_active = self.cleaned_data.get("is_active", True)
        if commit:
            user.save()
            role = self.cleaned_data.get("role")
            if role:
                group = Group.objects.filter(name__iexact=role).first()
                if not group:
                    group_name = "Gerant" if role == "gerant" else role.capitalize()
                    group = Group.objects.create(name=group_name)
                user.groups.add(group)
        return user
