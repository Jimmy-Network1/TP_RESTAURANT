from django import forms
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()


class LoginForm(forms.Form):
    username_or_email = forms.CharField(label="Email ou nom d’utilisateur")
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")

    def clean(self):
        cleaned = super().clean()
        user_id = cleaned.get("username_or_email")
        pwd = cleaned.get("password")
        user = None
        if user_id and pwd:
            try:
                user_obj = User.objects.get(email__iexact=user_id)
                username = user_obj.username
            except User.DoesNotExist:
                username = user_id
            user = authenticate(username=username, password=pwd)
            if not user:
                raise forms.ValidationError("Identifiants invalides.")
            if not user.is_active:
                raise forms.ValidationError("Compte désactivé.")
        cleaned["user"] = user
        return cleaned


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirmer le mot de passe")

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "username"]

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email déjà utilisé.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
