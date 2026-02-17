from django.contrib import admin

from .models import (
    KitchenStation,
    KitchenTicket,
    KitchenTicketItem,
    Recipe,
    RecipeIngredient,
    RecipeStep,
)


@admin.register(KitchenStation)
class KitchenStationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class KitchenTicketItemInline(admin.TabularInline):
    model = KitchenTicketItem
    extra = 1


@admin.register(KitchenTicket)
class KitchenTicketAdmin(admin.ModelAdmin):
    list_display = ('order', 'station', 'status', 'created_at')
    list_filter = ('status', 'station')
    inlines = [KitchenTicketItemInline]


class RecipeStepInline(admin.TabularInline):
    model = RecipeStep
    extra = 1


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('dish', 'servings', 'total_time_minutes')
    inlines = [RecipeStepInline, RecipeIngredientInline]
