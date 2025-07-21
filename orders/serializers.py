from rest_framework import serializers

from orders.models import CartItem, Cart, OrderItem, Order
from products.models import Product
from users.models import DeliveryContact
from users.serializers import DeliveryContactSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    shop = serializers.CharField(source='product.shop.name', read_only=True)
    unit_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True)
    total_price = serializers.ReadOnlyField(source='get_subtotal')

    class Meta:
        model = CartItem
        fields = [
            'product', # id товара
            'product_name',
            'shop',
            'unit_price',
            'quantity',
            'total_price',
        ]


class CartSerializer(serializers.ModelSerializer):
    cart_id = serializers.IntegerField(source='id', read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.ReadOnlyField(source='get_total')

    class Meta:
        model = Cart
        fields = ('cart_id', 'items', 'total')


class AddCartItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, data):
        # 1 Проверяем, существует ли товар по айди
        try:
            product = Product.objects.get(pk=data['product_id'])
        except Product.DoesNotExist:
            raise serializers.ValidationError('Товар не найден')

        # 2 Проверяем, достаточно ли товара на складе
        if data['quantity'] > product.quantity:
            raise serializers.ValidationError('Недостаточно товара на складе')

        return data


class RemoveCartItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, required=False)

    def validate_product_id(self, pk):
        if not Product.objects.filter(pk=pk).exists():
            raise serializers.ValidationError('Товар не найден')
        return pk


class ConfirmOrderSerializer(serializers.Serializer):
    cart_id = serializers.IntegerField()
    contact_id = serializers.IntegerField()

    def validate_cart_id(self, pk):
        user = self.context['request'].user
        if not Cart.objects.filter(pk=pk, user=user).exists():
            raise serializers.ValidationError('Корзина не найдена')
        return pk

    def validate_contact_id(self, pk):
        user = self.context['request'].user
        if not DeliveryContact.objects.filter(pk=pk, user=user).exists():
            raise serializers.ValidationError('Контакт не найден')
        return pk


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.CharField(source='product.name', read_only=True)
    unit_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    total_price = serializers.ReadOnlyField(source='get_total_price')

    class Meta:
        model = OrderItem
        fields = (
            'product',
            'unit_price',
            'quantity',
            'total_price',
        )


class OrderSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source='id', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    contact = DeliveryContactSerializer(read_only=True)
    total_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Order
        fields = (
            'order_id',
            'items',
            'contact',
            'total_amount',
            'status',
            'created_at',
            'updated_at',
        )


class OrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)

    def validate(self, data):
        order = self.context['order']
        new_state = data['status']
        old_state = order.status

        allowed = {
            Order.STATUS_NEW: {Order.STATUS_IN_PROGRESS, Order.STATUS_CANCELLED},
            Order.STATUS_IN_PROGRESS: {Order.STATUS_SHIPPED, Order.STATUS_CANCELLED},
            Order.STATUS_SHIPPED: {Order.STATUS_COMPLETED, Order.STATUS_CANCELLED},
            Order.STATUS_COMPLETED: set(),
            Order.STATUS_CANCELLED: set(),
        }
        if new_state not in allowed[old_state]:
            raise serializers.ValidationError(
                f"Невозможно перевести заказ в состояние {new_state}"
            )
        return data
