from decimal import Decimal

from django.conf import settings
from django.db import models

class Cart(models.Model):
    """
    Корзина текущих товаров у пользователя
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def add_item(self, product, qty=1):
        item, created = self.items.get_or_create(product=product, defaults={'quantity': qty})
        if not created:
            item.quantity += qty
            item.save(update_fields=['quantity'])
        return item

    def remove_item(self, product):
        self.items.filter(product=product).delete()

    def clear(self):
        self.items.all().delete()

    def get_total(self):
        total = Decimal('0')
        for item in self.items.select_related('product'):
            total += item.get_subtotal()
        return total

    def __str__(self):
        return f"Cart #{self.id} {self.user.email}"


class CartItem(models.Model):
    """
    Товары в корзине
    """
    cart = models.ForeignKey(
        'Cart',
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product')

    def get_subtotal(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


class Order(models.Model):
    """
    Заказ: привязан к пользователю и контакту доставки
    """
    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_SHIPPED = 'shipped'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_NEW, 'Новый'),
        (STATUS_IN_PROGRESS, 'В обработке'),
        (STATUS_SHIPPED, 'Отправлен'),
        (STATUS_COMPLETED, 'Завершен'),
        (STATUS_CANCELLED, 'Отменен'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    delivery_contact = models.ForeignKey(
        'users.DeliveryContact',
        on_delete=models.PROTECT,
        help_text='Контактная информация для доставки'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Общая сумма заказа'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def start_processing(self):
        """
        Переводит заказ из состояния NEW в IN_PROGRESS,
        посчитает итоговую сумму и сохраняет изменения
        """
        self.calculate_total()
        self.status = self.STATUS_IN_PROGRESS
        self.save(update_fields=['status', 'total_amount'])

    def __str__(self):
        return f"Order #{self.id} ({self.get_status_display()})"


class OrderItem(models.Model):
    """
    Товар в заказе с ценой и количеством
    """
    order = models.ForeignKey(
        'Order',
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Цена за единицу товара'
    )

    class Meta:
        unique_together = ('order', 'product')

    def __str__(self):
        return f"{self.quantity} x {self.product.name}, цена за единицу: {self.unit_price}"
