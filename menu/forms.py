from django import forms

from .models import Category, Dish


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'parent', 'is_active']


class DishForm(forms.ModelForm):
    class Meta:
        model = Dish
        fields = [
            'name',
            'description',
            'price',
            'photo',
            'category',
            'ingredients',
            'allergens',
            'tags',
            'prep_time_minutes',
            'availability',
            'cost_price',
            'margin_percent',
            'is_active',
        ]
        widgets = {
            'ingredients': forms.CheckboxSelectMultiple,
            'allergens': forms.Textarea(attrs={'rows': 2}),
            'tags': forms.Textarea(attrs={'rows': 2}),
        }
