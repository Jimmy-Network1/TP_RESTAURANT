from django.shortcuts import get_object_or_404, render

from django.utils.text import slugify

from menu.models import Category, Dish


def home(request):
    categories = Category.objects.all().order_by('name')[:6]
    popular_dishes = Dish.objects.select_related('category').order_by('-id')[:6]
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
    categories_qs = Category.objects.all().order_by('name')
    dishes_qs = Dish.objects.select_related('category').all().order_by('name')

    # Normalise catégories avec slug dérivé du nom (pas de champ slug en DB)
    categories = [
        {
            'id': c.id,
            'name': c.name,
            'slug': slugify(c.name),
        }
        for c in categories_qs
    ]

    if not categories:
        categories = [
            {'id': None, 'name': 'Grillades', 'slug': 'grillades'},
            {'id': None, 'name': 'Snacks', 'slug': 'snacks'},
            {'id': None, 'name': 'Desserts', 'slug': 'desserts'},
        ]

    if dishes_qs.exists():
        dishes = [
            {
                'id': d.id,
                'name': d.name,
                'price': d.price,
                'description': d.description,
                'image': getattr(d, 'photo', None) and d.photo.url or '',
                'category_slug': slugify(d.category.name),
                'available': d.availability == Dish.AVAILABILITY_IN_STOCK and d.is_active,
            }
            for d in dishes_qs
        ]
    else:
        dishes = [
            {
                'id': 1,
                'name': 'Poulet DG',
                'price': 4500,
                'description': 'Poulet braisé, banane plantain, légumes croquants.',
                'image': 'https://placehold.co/400x250',
                'category_slug': 'grillades',
                'available': True,
            },
            {
                'id': 2,
                'name': 'Ndolé crevettes',
                'price': 5200,
                'description': 'Feuilles de ndolé, crevettes, arachides grillées.',
                'image': 'https://placehold.co/400x250',
                'category_slug': 'grillades',
                'available': True,
            },
            {
                'id': 3,
                'name': 'Beignets haricots',
                'price': 1200,
                'description': 'BHB croustillant, piment doux maison.',
                'image': 'https://placehold.co/400x250',
                'category_slug': 'snacks',
                'available': True,
            },
            {
                'id': 4,
                'name': 'Ananas rôti',
                'price': 1800,
                'description': 'Ananas caramélisé, sirop gingembre, noix de coco.',
                'image': 'https://placehold.co/400x250',
                'category_slug': 'desserts',
                'available': True,
            },
        ]
    return render(
        request,
        'public/menu_list.html',
        {
            'categories': categories,
            'dishes': dishes,
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
    return render(
        request,
        'public/cart.html',
        {'cart_items': cart_items, 'cart_count': len(cart_items)},
    )


def checkout_view(request):
    cart_summary = request.session.get(
        'cart_summary',
        {'items': [], 'total': 0},
    )
    return render(
        request,
        'public/checkout.html',
        {'cart_summary': cart_summary, 'cart_count': len(cart_summary.get('items', []))},
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
