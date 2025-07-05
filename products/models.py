from django.db import models


class Product(models.Model):
    external_id = models.IntegerField(unique=True)
    category = models.ForeignKey(
        'products.Category',
        on_delete=models.PROTECT,
        related_name='products'
    )
    model = models.CharField(max_length=255)
    shop = models.ForeignKey(
        'shop.Shop',
        on_delete=models.CASCADE,
        related_name='products',
        help_text='Магазин, в котором продается товар'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    characteristics = models.JSONField(
        blank=True,
        null=True,
        help_text='Характеристики товара в виде словаря'
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_rrc = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def in_stock(self, qty=1):
        return self.quantity >= qty

    def decrease_stock(self, qty):
        if qty > self.quantity:
            raise ValueError('Недостаточно товара в наличии')
        self.quantity -= qty
        self.save(update_fields=['quantity'])

    def __str__(self):
        return f"{self.name} ({self.supplier.user.email})"


class Category(models.Model):
    """
    Хранит данные из shop1.yaml:
    external_id
    name
    """
    external_id = models.IntegerField(unique=True, help_text='ID из shop1.yaml')
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
