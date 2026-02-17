from django import forms
from django.forms import inlineformset_factory

from .models import Ingredient, PurchaseOrder, PurchaseOrderItem, StockMovement, Supplier


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_name', 'phone', 'email', 'address', 'notes']


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = [
            'name',
            'category',
            'unit',
            'quantity_in_stock',
            'alert_threshold',
            'unit_cost',
            'supplier',
            'storage_location',
            'expiry_date',
            'is_active',
        ]


class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = ['ingredient', 'movement_type', 'quantity', 'note']


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'status', 'total_amount', 'received_at']


class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = ['ingredient', 'quantity', 'unit_cost']


PurchaseOrderItemFormSet = inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderItem,
    form=PurchaseOrderItemForm,
    extra=1,
    can_delete=True,
)
