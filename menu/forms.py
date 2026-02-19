from django import forms

from .models import Category, Dish


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'parent', 'is_active']


class DishForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional_fields = [
            'ingredients',
            'allergens',
            'tags',
            'prep_time_minutes',
            'cost_price',
            'margin_percent',
        ]
        for name in optional_fields:
            if name in self.fields:
                self.fields[name].required = False
        for name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')
            field.widget.attrs.setdefault('placeholder', field.label)

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
