from django import forms
from .models import Table


class TableForm(forms.ModelForm):
    class Meta:
        model = Table
        fields = ["name", "zone", "capacity", "status", "active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "T12"}),
            "zone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Terrasse, Salle, VIP"}),
            "capacity": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class TableTransferForm(forms.Form):
    ACTION_CHOICES = (
        ("transfer", "Transférer commande"),
        ("merge", "Fusionner tables"),
    )
    action = forms.ChoiceField(choices=ACTION_CHOICES, widget=forms.RadioSelect)
    source = forms.ModelChoiceField(queryset=Table.objects.all(), label="Table source")
    destination = forms.ModelChoiceField(queryset=Table.objects.all(), label="Table destination")

    def clean(self):
        cleaned = super().clean()
        src = cleaned.get("source")
        dest = cleaned.get("destination")
        if src and dest and src == dest:
            raise forms.ValidationError("Choisissez deux tables différentes.")
        return cleaned
