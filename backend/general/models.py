from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.html import format_html



class Color(models.Model):
    name = models.CharField(max_length=100)
    hex_code=models.CharField(max_length=7, default='#FFFFFF')

    def __str__(self):
        return f"{self.name} ({self.hex_code})"

    def colored_circle(self):
        return format_html(
            '<span style="display: inline-block; width: 15px; height: 15px; border-radius: 50%; background: {}; border: 1px solid #ddd"></span> {}',
            self.hex_code,
            self.name
        )

class Size(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_detail', args=[str(self.pk)])

class ProductVariation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    size = models.ManyToManyField(Size)


    def __str__(self):
        return f"{self.product.name} - {self.color.name}"


class ProductImage(models.Model):
    image = models.ImageField(upload_to='product/')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)

    def __str__(self):
        return f"Изображение {self.product.name}.{self.color.name}"

class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )
    first_name = models.CharField(max_length=100)
    second_name = models.CharField(max_length=100)
    third_name = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, null=True, blank=True)
    date_birth = models.DateField()

class PickupPoint(models.Model):
    address = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.address

class Order(models.Model):
    TYPE_PAYMENT_CHOICES = [
        ("0", "Банковская карта "),
        ("1", "Наличные"),
    ]
    STATUS_CHOICES = [
        ("0", "Новая"),
        ("1", "В Обработке"),
        ("2", "Принята"),
        ("3", "Завершена"),
        ("4", "Отменена"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    address = models.ForeignKey(
        PickupPoint,
        on_delete=models.SET_NULL,
        null=True,
        blank=False
    )
    type_payment = models.CharField(max_length=1, choices=TYPE_PAYMENT_CHOICES)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='0')
    date_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    product = models.ManyToManyField(
        Product,
        related_name='orders'
    )
    cancel_reason = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"Заказ #{self.id} от {self.user.username}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # цена на момент заказа
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def total_price(self):
        return self.quantity * self.price

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Корзина {self.user.username}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def total_items(self):
        return self.items.count()

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def total_price(self):
        return self.product.price * self.quantity