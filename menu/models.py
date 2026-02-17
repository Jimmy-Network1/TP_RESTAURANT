from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Catégories'

    def __str__(self):
        return self.name


class Dish(models.Model):
    AVAILABILITY_IN_STOCK = 'in_stock'
    AVAILABILITY_OUT_OF_STOCK = 'out_of_stock'
    AVAILABILITY_SEASONAL = 'seasonal'

    AVAILABILITY_CHOICES = [
        (AVAILABILITY_IN_STOCK, 'En stock'),
        (AVAILABILITY_OUT_OF_STOCK, 'Rupture'),
        (AVAILABILITY_SEASONAL, 'Saisonnier'),
    ]

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    photo = models.ImageField(upload_to='dishes/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='dishes')
    ingredients = models.ManyToManyField('inventory.Ingredient', blank=True, related_name='dishes')
    allergens = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)
    prep_time_minutes = models.PositiveIntegerField(default=0)
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default=AVAILABILITY_IN_STOCK)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    margin_percent = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class DishVariant(models.Model):
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100)
    extra_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.dish.name} - {self.name}"


class DailyMenu(models.Model):
    name = models.CharField(max_length=150)
    date = models.DateField()
    dishes = models.ManyToManyField(Dish, related_name='daily_menus', blank=True)
    fixed_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Menus du jour'

    def __str__(self):
        return f"{self.name} ({self.date})"
