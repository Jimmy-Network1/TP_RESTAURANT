from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import UserProfile
from .forms import (
    KitchenStationForm,
    KitchenTicketForm,
    KitchenTicketItemFormSet,
    RecipeForm,
    RecipeIngredientFormSet,
    RecipeStepFormSet,
)
from .models import KitchenStation, KitchenTicket, Recipe


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_CHEF])
def board(request):
    tickets = KitchenTicket.objects.select_related('order').all().order_by('created_at')
    return render(request, 'kitchen/board.html', {'tickets': tickets})


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_CHEF])
def stations_list(request):
    stations = KitchenStation.objects.all().order_by('name')
    return render(request, 'kitchen/stations_list.html', {'stations': stations})


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_CHEF])
def stations_new(request):
    if request.method == 'POST':
        form = KitchenStationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('kitchen:stations')
    else:
        form = KitchenStationForm()
    return render(request, 'kitchen/stations_new.html', {'form': form})


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_CHEF])
def stations_edit(request, pk):
    station = get_object_or_404(KitchenStation, pk=pk)
    if request.method == 'POST':
        form = KitchenStationForm(request.POST, instance=station)
        if form.is_valid():
            form.save()
            return redirect('kitchen:stations')
    else:
        form = KitchenStationForm(instance=station)
    return render(request, 'kitchen/stations_edit.html', {'form': form, 'station': station})


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_CHEF])
def stations_delete(request, pk):
    station = get_object_or_404(KitchenStation, pk=pk)
    if request.method == 'POST':
        station.delete()
        return redirect('kitchen:stations')
    return render(request, 'kitchen/stations_delete.html', {'station': station})


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_CHEF])
def tickets_list(request):
    tickets = KitchenTicket.objects.select_related('order', 'station').all().order_by('-created_at')
    return render(request, 'kitchen/tickets_list.html', {'tickets': tickets})


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_CHEF])
def tickets_new(request):
    if request.method == 'POST':
        form = KitchenTicketForm(request.POST)
        formset = KitchenTicketItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            ticket = form.save()
            formset.instance = ticket
            formset.save()
            return redirect('kitchen:tickets')
    else:
        form = KitchenTicketForm()
        formset = KitchenTicketItemFormSet()
    return render(request, 'kitchen/tickets_new.html', {'form': form, 'formset': formset})


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_CHEF])
def tickets_edit(request, pk):
    ticket = get_object_or_404(KitchenTicket, pk=pk)
    if request.method == 'POST':
        form = KitchenTicketForm(request.POST, instance=ticket)
        formset = KitchenTicketItemFormSet(request.POST, instance=ticket)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('kitchen:tickets')
    else:
        form = KitchenTicketForm(instance=ticket)
        formset = KitchenTicketItemFormSet(instance=ticket)
    return render(request, 'kitchen/tickets_edit.html', {'form': form, 'formset': formset, 'ticket': ticket})


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_CHEF])
def tickets_delete(request, pk):
    ticket = get_object_or_404(KitchenTicket, pk=pk)
    if request.method == 'POST':
        ticket.delete()
        return redirect('kitchen:tickets')
    return render(request, 'kitchen/tickets_delete.html', {'ticket': ticket})


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_CHEF])
def recipes_list(request):
    recipes = Recipe.objects.select_related('dish').all().order_by('dish__name')
    return render(request, 'kitchen/recipes_list.html', {'recipes': recipes})


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_CHEF])
def recipes_new(request):
    if request.method == 'POST':
        form = RecipeForm(request.POST)
        step_formset = RecipeStepFormSet(request.POST)
        ingredient_formset = RecipeIngredientFormSet(request.POST)
        if form.is_valid() and step_formset.is_valid() and ingredient_formset.is_valid():
            recipe = form.save()
            step_formset.instance = recipe
            ingredient_formset.instance = recipe
            step_formset.save()
            ingredient_formset.save()
            return redirect('kitchen:recipes')
    else:
        form = RecipeForm()
        step_formset = RecipeStepFormSet()
        ingredient_formset = RecipeIngredientFormSet()
    return render(
        request,
        'kitchen/recipes_new.html',
        {'form': form, 'step_formset': step_formset, 'ingredient_formset': ingredient_formset},
    )


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_CHEF])
def recipes_edit(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == 'POST':
        form = RecipeForm(request.POST, instance=recipe)
        step_formset = RecipeStepFormSet(request.POST, instance=recipe)
        ingredient_formset = RecipeIngredientFormSet(request.POST, instance=recipe)
        if form.is_valid() and step_formset.is_valid() and ingredient_formset.is_valid():
            form.save()
            step_formset.save()
            ingredient_formset.save()
            return redirect('kitchen:recipes')
    else:
        form = RecipeForm(instance=recipe)
        step_formset = RecipeStepFormSet(instance=recipe)
        ingredient_formset = RecipeIngredientFormSet(instance=recipe)
    return render(
        request,
        'kitchen/recipes_edit.html',
        {'form': form, 'step_formset': step_formset, 'ingredient_formset': ingredient_formset, 'recipe': recipe},
    )


@role_required([UserProfile.ROLE_ADMIN, UserProfile.ROLE_CHEF])
def recipes_delete(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == 'POST':
        recipe.delete()
        return redirect('kitchen:recipes')
    return render(request, 'kitchen/recipes_delete.html', {'recipe': recipe})
