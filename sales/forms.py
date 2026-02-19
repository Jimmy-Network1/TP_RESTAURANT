from django import forms
from django.forms import inlineformset_factory

from .models import Order, OrderItem, Payment, Table


class TableForm(forms.ModelForm):
    class Meta:
        model = Table
        fields = ['name', 'zone', 'capacity', 'status']


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'order_type',
            'status',
            'table',
            'customer_name',
            'customer_phone',
            'delivery_address',
            'assigned_delivery',
            'discount_amount',
            'tax_amount',
            'tip_amount',
        ]


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['dish', 'quantity', 'unit_price', 'note']


OrderItemFormSet = inlineformset_factory(
    Order,
    OrderItem,
    form=OrderItemForm,
    extra=1,
    can_delete=True,
)


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['order', 'method', 'amount']


class TableTransferForm(forms.Form):
    ACTION_CHOICES = [
        ('transfer', 'Transférer la commande'),
        ('merge', 'Fusionner les tables'),
    ]

    source = forms.ModelChoiceField(queryset=Table.objects.all(), label="Table source")
    destination = forms.ModelChoiceField(queryset=Table.objects.all(), label="Table destination")
    action = forms.ChoiceField(choices=ACTION_CHOICES, initial='transfer', label="Action")

    def clean(self):
        cleaned = super().clean()
        src = cleaned.get('source')
        dst = cleaned.get('destination')
        if src and dst and src == dst:
            self.add_error('destination', "Choisissez une table différente.")
        return cleaned
