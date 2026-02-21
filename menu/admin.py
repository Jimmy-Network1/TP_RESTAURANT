from django.contrib import admin

from .models import Category, Dish, DishOption


class DishOptionInline(admin.TabularInline):
    model = DishOption
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active")
    search_fields = ("name",)
    list_filter = ("is_active",)
    ordering = ("name",)


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "price", "availability", "is_active")
    search_fields = ("name", "category__name")
    list_filter = ("availability", "is_active", "category")
    ordering = ("name",)
    inlines = [DishOptionInline]


@admin.register(DishOption)
class DishOptionAdmin(admin.ModelAdmin):
    list_display = ("id", "dish", "name", "extra_price")
    search_fields = ("dish__name", "name")
    list_filter = ("dish",)
