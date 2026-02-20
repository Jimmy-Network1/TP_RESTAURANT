from django import forms
from .models import Ingredient, StockMovement


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ["name", "unit", "quantity_in_stock", "alert_threshold", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Riz"}),
            "unit": forms.Select(attrs={"class": "form-control"}),
            "quantity_in_stock": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "alert_threshold": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = ["ingredient", "movement_type", "quantity", "note"]
        widgets = {
            "ingredient": forms.Select(attrs={"class": "form-control"}),
            "movement_type": forms.Select(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "note": forms.TextInput(attrs={"class": "form-control", "placeholder": "Achat, perte, ajustement"}),
        }
