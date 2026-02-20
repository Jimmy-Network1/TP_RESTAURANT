from django import forms
from .models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["order_type", "table", "customer", "status", "note"]
        widgets = {
            "order_type": forms.Select(attrs={"class": "form-control"}),
            "table": forms.Select(attrs={"class": "form-control"}),
            "customer": forms.Select(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "note": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Ex: sans piment"}),
        }

    def clean(self):
        cleaned = super().clean()
        order_type = cleaned.get("order_type")
        table = cleaned.get("table")
        if order_type == Order.TYPE_DINE_IN and not table:
            self.add_error("table", "La table est obligatoire pour une commande sur place.")
        if order_type == Order.TYPE_DINE_IN and table and table.status == "reserved":
            self.add_error("table", "Table réservée : check-in requis avant commande.")
        return cleaned
