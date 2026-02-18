from decimal import Decimal

from django.contrib import messages
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from menu.models import Category, Dish
from sales.models import Order, OrderItem


PHOTO_KEYWORDS = [
    ('burger', 'burger à la viande de bœuf.jpg'),
    ('taco', 'tacos à la viande de bœuf.jpg'),
    ('poulet', 'poulet rôti aux thym.jpg'),
    ('lasagne', 'lasagnes classiques.jpg'),
    ('ramen', 'Ramen.jpg'),
    ('salade', 'Macédoine aux légumes.jpg'),
    ('ndole', 'Ndole plantain.jpeg'),
    ('eru', 'Eru.jpeg'),
    ('bongo', 'Bongo tchobi .jpeg'),
    ('pistache', 'Mets de pistache.jpeg'),
    ('poisson', 'Poisson Braiser.jpeg'),
    ('bissap', 'Folere bissap jus.jpeg'),
    ('baobab', 'Jus de baobab.jpeg'),
    ('corossol', 'Jus de corrosol .jpeg'),
    ('papaye', 'Jus de papaye .jpeg'),
    ('vin', 'Vin de palme .jpeg'),
]


def _fallback_image_for(name: str) -> str:
    lower = name.lower()
    for key, filename in PHOTO_KEYWORDS:
        if key in lower:
            return static(f"photos/{filename}")
    return static("photos/poulet rôti aux amandes.jpg")


def _sample_categories():
    return [
        {'id': None, 'name': 'Plats locaux', 'slug': 'plats-locaux'},
        {'id': None, 'name': 'Plats européens', 'slug': 'plats-europeens'},
        {'id': None, 'name': 'Plats chauds', 'slug': 'plats-chauds'},
        {'id': None, 'name': 'Burgers', 'slug': 'burgers'},
        {'id': None, 'name': 'Tacos', 'slug': 'tacos'},
        {'id': None, 'name': 'Pâtes & gratins', 'slug': 'pates'},
        {'id': None, 'name': 'Veggie', 'slug': 'veggie'},
        {'id': None, 'name': 'Boissons', 'slug': 'boissons'},
    ]


def _sample_dishes():
    return [
        # Plats locaux
        {
            'id': 201,
            'name': 'Ndolé plantain',
            'price': 5500,
            'description': 'Feuilles de ndolé, arachides, crevettes, plantains mûrs.',
            'image': static('photos/Ndole plantain.jpeg'),
            'category_slug': 'plats-locaux',
            'available': True,
        },
        {
            'id': 202,
            'name': 'Bongo Tchobi',
            'price': 5200,
            'description': 'Sauce noire d’épices bongo, poisson braisé, bâtons de manioc.',
            'image': static('photos/Bongo tchobi .jpeg'),
            'category_slug': 'plats-locaux',
            'available': True,
        },
        {
            'id': 203,
            'name': 'Eru & water fufu',
            'price': 5000,
            'description': 'Légumes Eru, peau de bœuf, crevettes séchées, bâtons.',
            'image': static('photos/Eru.jpeg'),
            'category_slug': 'plats-locaux',
            'available': True,
        },
        {
            'id': 204,
            'name': 'Poisson braisé',
            'price': 6200,
            'description': 'Poisson mariné aux épices vertes, grillé au feu de bois.',
            'image': static('photos/Poisson Braiser.jpeg'),
            'category_slug': 'plats-locaux',
            'available': True,
        },
        {
            'id': 205,
            'name': 'Sauce pistache & plantain',
            'price': 5400,
            'description': 'Sauce aux graines de courge, pilon de plantain.',
            'image': static('photos/Sauce de pistache avec plantain.jpeg'),
            'category_slug': 'plats-locaux',
            'available': True,
        },

        # Boissons locales
        {
            'id': 301,
            'name': 'Foléré (bissap)',
            'price': 1500,
            'description': 'Jus d’hibiscus, gingembre, citron vert.',
            'image': static('photos/Folere bissap jus.jpeg'),
            'category_slug': 'boissons',
            'available': True,
        },
        {
            'id': 302,
            'name': 'Jus de corossol',
            'price': 1800,
            'description': 'Corossol frais mixé, touche de vanille.',
            'image': static('photos/Jus de corrosol .jpeg'),
            'category_slug': 'boissons',
            'available': True,
        },
        {
            'id': 303,
            'name': 'Vin de palme',
            'price': 2000,
            'description': 'Vin de palme traditionnel, servi frais.',
            'image': static('photos/Vin de palme .jpeg'),
            'category_slug': 'boissons',
            'available': True,
        },

        {
            'id': 101,
            'name': 'Burger bœuf braisé',
            'price': 5200,
            'description': 'Steak mariné, cheddar affiné, oignons caramélisés.',
            'image': static('photos/burger à la viande de bœuf.jpg'),
            'category_slug': 'burgers',
            'available': True,
        },
        {
            'id': 102,
            'name': 'Burger croustillant poulet',
            'price': 4800,
            'description': 'Poulet pané, sauce fumée, frites maison.',
            'image': static('photos/burger poulet+ frittes.jpg'),
            'category_slug': 'burgers',
            'available': True,
        },
        {
            'id': 103,
            'name': 'Tacos bœuf grillé',
            'price': 3900,
            'description': 'Bœuf mariné, pico de gallo, crème citron vert.',
            'image': static('photos/tacos à la viande de bœuf.jpg'),
            'category_slug': 'tacos',
            'available': True,
        },
        {
            'id': 104,
            'name': 'Tacos veggie',
            'price': 3600,
            'description': 'Haricots noirs, maïs rôti, pickles maison.',
            'image': static('photos/tacos aux végétaux.jpg'),
            'category_slug': 'tacos',
            'available': True,
        },
        {
            'id': 105,
            'name': 'Ramen coco-gingembre',
            'price': 5500,
            'description': 'Bouillon parfumé, poulet confit, œuf mollet.',
            'image': static('photos/Ramen.jpg'),
            'category_slug': 'plats-europeens',
            'available': True,
        },
        {
            'id': 106,
            'name': 'Poulet rôti au thym',
            'price': 4500,
            'description': 'Marinade citron thym, pommes grenailles.',
            'image': static('photos/poulet rôti aux thym.jpg'),
            'category_slug': 'plats-chauds',
            'available': True,
        },
        {
            'id': 107,
            'name': 'Katsu poulet pané',
            'price': 4300,
            'description': 'Filet pané panko, sauce tonkatsu, coleslaw.',
            'image': static('photos/poulet pané.jpg'),
            'category_slug': 'plats-europeens',
            'available': True,
        },
        {
            'id': 108,
            'name': 'Lasagnes classico',
            'price': 5200,
            'description': 'Bolognaise mijotée, parmesan gratiné.',
            'image': static('photos/lasagnes classiques.jpg'),
            'category_slug': 'pates',
            'available': True,
        },
        {
            'id': 109,
            'name': 'Lasagnes ricotta & aubergines',
            'price': 5400,
            'description': 'Aubergines rôties, ricotta fraîche, basilic.',
            'image': static('photos/lasagnes à la ricotta et aux aubergines.jpg'),
            'category_slug': 'pates',
            'available': True,
        },
        {
            'id': 110,
            'name': 'Macédoine fraîche',
            'price': 2900,
            'description': 'Légumes croquants, vinaigrette moutarde douce.',
            'image': static('photos/Macédoine aux légumes.jpg'),
            'category_slug': 'veggie',
            'available': True,
        },
        {
            'id': 111,
            'name': 'Poulet rôti aux amandes',
            'price': 4700,
            'description': 'Éclats d’amandes, jus corsé, semoule moelleuse.',
            'image': static('photos/poulet rôti aux amandes.jpg'),
            'category_slug': 'plats-chauds',
            'available': True,
        },
        {
            'id': 112,
            'name': 'Tacos poulet fumé',
            'price': 3800,
            'description': 'Poulet fumé, sauce yaourt coriandre, pickles.',
            'image': static('photos/tacos au poulet.jpg'),
            'category_slug': 'tacos',
            'available': True,
        },
    ]


def home(request):
    categories = Category.objects.all().order_by('name')[:6]
    popular_qs = Dish.objects.select_related('category').order_by('-id')[:6]
    if popular_qs.exists():
        popular_dishes = [
            {
                'id': d.id,
                'name': d.name,
                'price': d.price,
                'description': d.description,
                'image': d.photo.url if getattr(d, 'photo', None) else _fallback_image_for(d.name),
                'category_slug': slugify(d.category.name) if d.category else '',
                'available': d.availability == Dish.AVAILABILITY_IN_STOCK and d.is_active,
            }
            for d in popular_qs
        ]
    else:
        popular_dishes = _sample_dishes()[:6]

    # Complète si peu de plats en base
    if len(popular_dishes) < 6:
        existing = {d['name'].lower() for d in popular_dishes}
        for sd in _sample_dishes():
            if sd['name'].lower() not in existing:
                popular_dishes.append(sd)
            if len(popular_dishes) >= 6:
                break
    return render(
        request,
        'home.html',
        {
            'popular_dishes': popular_dishes,
            'categories': categories,
            'cart_count': request.session.get('cart_count', 0),
        },
    )


def menu_list(request):
    query = request.GET.get('q', '').strip()
    categories_qs = Category.objects.all().order_by('name')
    dishes_qs = Dish.objects.select_related('category').all().order_by('name')
    if query:
        dishes_qs = dishes_qs.filter(models.Q(name__icontains=query) | models.Q(description__icontains=query))

    # Normalise catégories avec slug dérivé du nom (pas de champ slug en DB)
    categories = [
        {'id': c.id, 'name': c.name, 'slug': slugify(c.name)} for c in categories_qs
    ]

    dishes = []
    for d in dishes_qs:
        dishes.append(
            {
                'id': d.id,
                'name': d.name,
                'price': d.price,
                'description': d.description,
                'image': d.photo.url if getattr(d, 'photo', None) else _fallback_image_for(d.name),
                'category_slug': slugify(d.category.name) if d.category else '',
                'available': d.availability == Dish.AVAILABILITY_IN_STOCK and d.is_active,
            }
        )

    # Complète avec les plats de démo pour garder un menu fourni
    sample_dishes = _sample_dishes()
    if query:
        q_low = query.lower()
        sample_dishes = [d for d in sample_dishes if q_low in d['name'].lower() or q_low in d['description'].lower()]

    existing_names = {d['name'].lower() for d in dishes}
    for sd in sample_dishes:
        if sd['name'].lower() not in existing_names:
            dishes.append(sd)
            existing_names.add(sd['name'].lower())

    # Catégories : ajoute celles des samples si absentes
    if not categories:
        categories = _sample_categories()
    else:
        existing_slugs = {c['slug'] for c in categories}
        for sc in _sample_categories():
            if sc['slug'] not in existing_slugs:
                categories.append(sc)
                existing_slugs.add(sc['slug'])

    return render(
        request,
        'public/menu_list.html',
        {
            'categories': categories,
            'dishes': dishes,
            'search_query': query,
            'cart_count': request.session.get('cart_count', 0),
        },
    )


def dish_detail(request, pk):
    dish = get_object_or_404(Dish, pk=pk)
    return render(
        request,
        'public/dish_detail.html',
        {'dish': dish, 'cart_count': request.session.get('cart_count', 0)},
    )


def cart_view(request):
    cart_items = request.session.get('cart_items', [])
    total = sum(Decimal(str(item['price'])) * item['qty'] for item in cart_items)
    return render(
        request,
        'public/cart.html',
        {'cart_items': cart_items, 'cart_count': len(cart_items), 'cart_total': total},
    )


def checkout_view(request):
    cart_items = request.session.get('cart_items', [])
    total = sum(Decimal(str(item['price'])) * item['qty'] for item in cart_items)
    if request.method == 'POST':
        mode = request.POST.get('mode', 'onsite')
        name = request.POST.get('name', '')
        phone = request.POST.get('phone', '')
        address = request.POST.get('address', '')
        if not cart_items:
            messages.error(request, "Panier vide.")
            return redirect('public:cart')

        # S'assure que chaque plat existe en base (utile pour les plats de démonstration)
        default_cat, _ = Category.objects.get_or_create(name="Classiques")
        for item in cart_items:
            dish_obj = Dish.objects.filter(pk=item['id']).first()
            if not dish_obj:
                dish_obj = Dish.objects.create(
                    id=item['id'],
                    name=item['name'],
                    price=Decimal(str(item['price'])),
                    description=item.get('description', ''),
                    category=default_cat,
                    availability=Dish.AVAILABILITY_IN_STOCK,
                    is_active=True,
                )
                item['id'] = dish_obj.id  # sync session in case id was None

        order = Order.objects.create(
            order_type={
                'delivery': Order.TYPE_DELIVERY,
                'pickup': Order.TYPE_TAKEAWAY,
                'onsite': Order.TYPE_DINE_IN,
            }.get(mode, Order.TYPE_DINE_IN),
            status=Order.STATUS_SENT,
            customer_name=name,
            customer_phone=phone,
            delivery_address=address if mode == 'delivery' else '',
            total_amount=total,
            subtotal=total,
        )
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                dish_id=item['id'],
                quantity=item['qty'],
                unit_price=Decimal(str(item['price'])),
            )
        request.session['cart_items'] = []
        request.session['cart_count'] = 0
        request.session['order_confirm'] = {
            'number': order.id,
            'status': 'En attente',
            'eta': '30 min',
        }
        return redirect('public:order_confirm')

    cart_summary = {'items': cart_items, 'total': total}
    return render(
        request,
        'public/checkout.html',
        {'cart_summary': cart_summary, 'cart_count': len(cart_items)},
    )


def order_confirm_view(request):
    order = request.session.get(
        'order_confirm',
        {'number': 'A123', 'status': 'En attente', 'eta': '30 min'},
    )
    return render(
        request,
        'public/order_confirm.html',
        {'order': order, 'cart_count': 0},
    )


def reservation_form(request):
    return render(request, 'public/reservations.html', {'cart_count': request.session.get('cart_count', 0)})


@require_POST
def cart_add(request, pk):
    try:
        dish = Dish.objects.get(pk=pk)
        price = dish.price
        name = dish.name
        dish_id = dish.id
    except Dish.DoesNotExist:
        sample = next((d for d in _sample_dishes() if d['id'] == pk), None)
        if not sample:
            messages.error(request, "Plat introuvable.")
            return redirect(request.META.get('HTTP_REFERER', 'public:menu'))
        price = sample['price']
        name = sample['name']
        dish_id = sample['id']
    cart = request.session.get('cart_items', [])
    qty = int(request.POST.get('qty', 1))
    qty = max(1, qty)
    for item in cart:
        if item['id'] == dish_id:
            item['qty'] += qty
            break
    else:
        cart.append({'id': dish_id, 'name': name, 'price': float(price), 'qty': qty})
    request.session['cart_items'] = cart
    request.session['cart_count'] = sum(i['qty'] for i in cart)
    messages.success(request, f"{name} ajouté au panier.")
    return redirect(request.META.get('HTTP_REFERER', 'public:menu'))


@require_POST
def cart_add_ajax(request, pk):
    dish = get_object_or_404(Dish, pk=pk)
    cart = request.session.get('cart_items', [])
    qty = int(request.POST.get('qty', 1))
    qty = max(1, qty)
    for item in cart:
        if item['id'] == dish.id:
            item['qty'] += qty
            break
    else:
        cart.append({'id': dish.id, 'name': dish.name, 'price': float(dish.price), 'qty': qty})
    request.session['cart_items'] = cart
    request.session['cart_count'] = sum(i['qty'] for i in cart)
    total = sum(Decimal(str(i['price'])) * i['qty'] for i in cart)
    return JsonResponse({'success': True, 'cart_count': request.session['cart_count'], 'cart_total': float(total)})


@require_POST
def cart_update(request):
    action = request.POST.get('action')
    dish_id = int(request.POST.get('id', 0))
    cart = request.session.get('cart_items', [])
    new_cart = []
    removed = False
    new_qty = None
    for item in cart:
        if item['id'] == dish_id:
            if action == 'plus':
                item['qty'] += 1
            elif action == 'minus':
                item['qty'] = max(1, item['qty'] - 1)
            elif action == 'remove':
                removed = True
                continue
            new_qty = item['qty']
        new_cart.append(item)
    request.session['cart_items'] = new_cart
    request.session['cart_count'] = sum(i['qty'] for i in new_cart)
    total = sum(Decimal(str(i['price'])) * i['qty'] for i in new_cart)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(
            {
                'success': True,
                'cart_count': request.session['cart_count'],
                'cart_total': float(total),
                'removed': removed,
                'item_qty': new_qty,
            }
        )
    return redirect('public:cart')
