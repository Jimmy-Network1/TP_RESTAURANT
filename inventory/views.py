from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    IngredientForm,
    PurchaseOrderForm,
    PurchaseOrderItemFormSet,
    StockMovementForm,
    SupplierForm,
)
from .models import Ingredient, PurchaseOrder, StockMovement, Supplier


def ingredients_list(request):
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    ingredients = Ingredient.objects.select_related('supplier').all().order_by('name')
    if q:
        ingredients = ingredients.filter(
            Q(name__icontains=q) | Q(category__icontains=q) | Q(supplier__name__icontains=q)
        )
    if status == 'low':
        ingredients = ingredients.filter(quantity_in_stock__lte=F('alert_threshold'))
    stats = {
        'total': ingredients.count(),
        'low': ingredients.filter(quantity_in_stock__lte=F('alert_threshold')).count(),
        'active': ingredients.filter(is_active=True).count(),
    }
    return render(
        request,
        'inventory/ingredients_list.html',
        {'ingredients': ingredients, 'q': q, 'status': status, 'stats': stats},
    )


def ingredients_new(request):
    if request.method == 'POST':
        form = IngredientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inventory:ingredients')
    else:
        form = IngredientForm()
    return render(request, 'inventory/ingredients_new.html', {'form': form})


def ingredients_edit(request, pk):
    ingredient = get_object_or_404(Ingredient, pk=pk)
    if request.method == 'POST':
        form = IngredientForm(request.POST, instance=ingredient)
        if form.is_valid():
            form.save()
            return redirect('inventory:ingredients')
    else:
        form = IngredientForm(instance=ingredient)
    return render(request, 'inventory/ingredients_edit.html', {'form': form, 'ingredient': ingredient})


def ingredients_delete(request, pk):
    ingredient = get_object_or_404(Ingredient, pk=pk)
    if request.method == 'POST':
        ingredient.delete()
        return redirect('inventory:ingredients')
    return render(request, 'inventory/ingredients_delete.html', {'ingredient': ingredient})

def movements_list(request):
    date_from = request.GET.get('from')
    date_to = request.GET.get('to')
    movements = StockMovement.objects.select_related('ingredient').all().order_by('-created_at')
    if date_from:
        movements = movements.filter(created_at__date__gte=date_from)
    if date_to:
        movements = movements.filter(created_at__date__lte=date_to)
    return render(request, 'inventory/movements_list.html', {'movements': movements, 'date_from': date_from, 'date_to': date_to})


def movements_new(request):
    if request.method == 'POST':
        form = StockMovementForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inventory:movements')
    else:
        form = StockMovementForm()
    return render(request, 'inventory/movements_new.html', {'form': form})

def suppliers_list(request):
    suppliers = Supplier.objects.all().order_by('name')
    return render(request, 'inventory/suppliers_list.html', {'suppliers': suppliers})


def suppliers_new(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inventory:suppliers')
    else:
        form = SupplierForm()
    return render(request, 'inventory/suppliers_new.html', {'form': form})


def suppliers_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            return redirect('inventory:suppliers')
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'inventory/suppliers_edit.html', {'form': form, 'supplier': supplier})


def suppliers_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.delete()
        return redirect('inventory:suppliers')
    return render(request, 'inventory/suppliers_delete.html', {'supplier': supplier})


def purchase_orders_list(request):
    purchase_orders = PurchaseOrder.objects.select_related('supplier').all().order_by('-created_at')
    return render(request, 'inventory/purchase_orders_list.html', {'purchase_orders': purchase_orders})


def purchase_orders_new(request):
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        formset = PurchaseOrderItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            purchase_order = form.save()
            formset.instance = purchase_order
            formset.save()
            return redirect('inventory:purchase_orders')
    else:
        form = PurchaseOrderForm()
        formset = PurchaseOrderItemFormSet()
    return render(
        request,
        'inventory/purchase_orders_new.html',
        {'form': form, 'formset': formset},
    )


def purchase_orders_edit(request, pk):
    purchase_order = get_object_or_404(PurchaseOrder, pk=pk)
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, instance=purchase_order)
        formset = PurchaseOrderItemFormSet(request.POST, instance=purchase_order)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('inventory:purchase_orders')
    else:
        form = PurchaseOrderForm(instance=purchase_order)
        formset = PurchaseOrderItemFormSet(instance=purchase_order)
    return render(
        request,
        'inventory/purchase_orders_edit.html',
        {'form': form, 'formset': formset, 'purchase_order': purchase_order},
    )


def purchase_orders_delete(request, pk):
    purchase_order = get_object_or_404(PurchaseOrder, pk=pk)
    if request.method == 'POST':
        purchase_order.delete()
        return redirect('inventory:purchase_orders')
    return render(request, 'inventory/purchase_orders_delete.html', {'purchase_order': purchase_order})


def alerts(request):
    low_stock = Ingredient.objects.filter(quantity_in_stock__lte=F('alert_threshold')).order_by('name')
    return render(request, 'inventory/alerts.html', {'low_stock': low_stock})
