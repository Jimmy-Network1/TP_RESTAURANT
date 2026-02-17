from django import forms
from django.forms import inlineformset_factory

from .models import KitchenStation, KitchenTicket, KitchenTicketItem, Recipe, RecipeIngredient, RecipeStep


class KitchenStationForm(forms.ModelForm):
    class Meta:
        model = KitchenStation
        fields = ['name', 'description']


class KitchenTicketForm(forms.ModelForm):
    class Meta:
        model = KitchenTicket
        fields = ['order', 'station', 'status', 'note', 'started_at', 'ready_at']


class KitchenTicketItemForm(forms.ModelForm):
    class Meta:
        model = KitchenTicketItem
        fields = ['dish', 'quantity', 'note']


KitchenTicketItemFormSet = inlineformset_factory(
    KitchenTicket,
    KitchenTicketItem,
    form=KitchenTicketItemForm,
    extra=1,
    can_delete=True,
)


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['dish', 'description', 'servings', 'total_time_minutes', 'notes']


class RecipeStepForm(forms.ModelForm):
    class Meta:
        model = RecipeStep
        fields = ['step_number', 'instruction', 'time_minutes']


class RecipeIngredientForm(forms.ModelForm):
    class Meta:
        model = RecipeIngredient
        fields = ['ingredient', 'quantity', 'unit']


RecipeStepFormSet = inlineformset_factory(
    Recipe,
    RecipeStep,
    form=RecipeStepForm,
    extra=1,
    can_delete=True,
)

RecipeIngredientFormSet = inlineformset_factory(
    Recipe,
    RecipeIngredient,
    form=RecipeIngredientForm,
    extra=1,
    can_delete=True,
)
