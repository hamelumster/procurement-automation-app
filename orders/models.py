from decimal import Decimal

from django.conf import settings
from django.db import models

from products.models import Product
from shops.models import Shop


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
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Цена за единицу товара на момент добавления в корзину'
    )

    class Meta:
        unique_together = ('cart', 'product')

    def get_subtotal(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


class StatusMixin(models.Model):
    """
    Абстрактный класс с константами статусов и методами их изменения.
    """
    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_SHIPPED = 'shipped'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_NEW, 'Новый'),
        (STATUS_IN_PROGRESS, 'В обработке'),
        (STATUS_SHIPPED, 'Отправлен'),
        (STATUS_COMPLETED, 'Завершён'),
        (STATUS_CANCELLED, 'Отменён'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        help_text='Текущий статус'
    )

    class Meta:
        abstract = True

    def set_status(self, new_status):
        if new_status not in dict(self.STATUS_CHOICES):
            raise ValueError(f'Неверный статус: {new_status}')
        self.status = new_status
        # при изменении статуса автоматически обновим метку
        self.save(update_fields=['status'])

    def start_processing(self):
        self.set_status(self.STATUS_IN_PROGRESS)

    def mark_shipped(self):
        self.set_status(self.STATUS_SHIPPED)

    def complete(self):
        self.set_status(self.STATUS_COMPLETED)

    def cancel(self):
        self.set_status(self.STATUS_CANCELLED)


class Order(StatusMixin):
    """
    Общий заказ, объединяющий подзаказы по магазинам.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    delivery_contact = models.ForeignKey(
        'users.DeliveryContact',
        on_delete=models.PROTECT
    )
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_total(self):
        # суммируем суммы всех ShopOrder
        total = sum(
            so.calculate_total()
            for so in self.shop_orders.all()
        )
        self.total_amount = total
        self.save(update_fields=['total_amount'])
        return total

    def __str__(self):
        return f"Order #{self.id} ({self.get_status_display()})"


class ShopOrder(StatusMixin):
    """
    Подзаказ конкретного магазина в рамках одного Order.
    """
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name='shop_orders'
    )
    shop = models.ForeignKey(
        Shop, on_delete=models.PROTECT,
        related_name='shop_orders'
    )
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('order', 'shop'),)

    def calculate_total(self):
        total = sum(
            item.quantity * item.unit_price
            for item in self.items.all()
        )
        self.total_amount = total
        self.save(update_fields=['total_amount'])
        return total

    def __str__(self):
        return f"ShopOrder #{self.id} for {self.shop.name}"


class ShopOrderItem(models.Model):
    """
    Товар в конкретном ShopOrder.
    """
    shop_order = models.ForeignKey(
        ShopOrder, on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = (('shop_order', 'product'),)

    def get_total_price(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


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

    def get_total_price(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.quantity} x {self.product.name}, цена за единицу: {self.unit_price}"
