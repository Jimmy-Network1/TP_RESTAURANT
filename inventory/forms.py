from django import forms
from .models import Ingredient, StockMovement


class IngredientForm(forms.ModelForm):
    def clean_quantity_in_stock(self):
        qty = self.cleaned_data.get("quantity_in_stock")
        if qty is not None and qty < 0:
            raise forms.ValidationError("Le stock ne peut pas être négatif.")
        return qty

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
    def clean(self):
        cleaned = super().clean()
        qty = cleaned.get("quantity")
        mtype = cleaned.get("movement_type")
        note = (cleaned.get("note") or "").strip()
        if qty is None or qty == 0:
            self.add_error("quantity", "La quantité doit être différente de 0.")
        if mtype in [StockMovement.TYPE_IN, StockMovement.TYPE_OUT] and qty is not None and qty < 0:
            self.add_error("quantity", "La quantité doit être positive.")
        if not note:
            self.add_error("note", "Le motif est obligatoire.")
        return cleaned

    class Meta:
        model = StockMovement
        fields = ["ingredient", "movement_type", "quantity", "note"]
        widgets = {
            "ingredient": forms.Select(attrs={"class": "form-control"}),
            "movement_type": forms.Select(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "note": forms.TextInput(attrs={"class": "form-control", "placeholder": "Achat, perte, ajustement"}),
        }
