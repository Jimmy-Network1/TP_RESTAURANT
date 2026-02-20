from django import forms

from .models import Category, Dish, DishOption


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description", "is_active"]


class DishForm(forms.ModelForm):
    class Meta:
        model = Dish
        fields = ["name", "category", "price", "description", "photo", "availability", "is_active"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class DishOptionForm(forms.ModelForm):
    class Meta:
        model = DishOption
        fields = ["dish", "name", "extra_price"]
