from django.contrib import admin

from .models import Category, DailyMenu, Dish, DishVariant


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


class DishVariantInline(admin.TabularInline):
    model = DishVariant
    extra = 1


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'availability', 'is_active')
    list_filter = ('availability', 'is_active', 'category')
    search_fields = ('name', 'description')
    inlines = [DishVariantInline]


@admin.register(DailyMenu)
class DailyMenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'fixed_price', 'is_active')
    list_filter = ('is_active', 'date')
    search_fields = ('name',)
