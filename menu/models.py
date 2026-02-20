from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Dish(models.Model):
    AVAILABILITY_IN_STOCK = "in_stock"
    AVAILABILITY_OUT = "out"
    AVAILABILITY_SEASONAL = "seasonal"
    AVAILABILITY_CHOICES = [
        (AVAILABILITY_IN_STOCK, "Disponible"),
        (AVAILABILITY_OUT, "Indisponible"),
        (AVAILABILITY_SEASONAL, "Saisonnier"),
    ]

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="dishes")
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    photo = models.ImageField(upload_to="dishes/", blank=True, null=True)
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default=AVAILABILITY_IN_STOCK)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class DishOption(models.Model):
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name="options")
    name = models.CharField(max_length=120)
    extra_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.name} (+{self.extra_price})"
