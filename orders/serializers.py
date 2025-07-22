from rest_framework import serializers

from orders.models import CartItem, Cart, OrderItem, Order, ShopOrderItem, ShopOrder
from products.models import Product
from users.models import DeliveryContact
from users.serializers import DeliveryContactSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source='product.id', read_only=True)
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
            'product_id',
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
    shop = serializers.CharField(
        source='product.shop.name',
        read_only=True,
        help_text='Название магазина'
    )
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
            'shop',
            'product',
            'unit_price',
            'quantity',
            'total_price',
        )


class ShopOrderItemSerializer(serializers.ModelSerializer):
    product = serializers.CharField(source='product.name', read_only=True)
    unit_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    quantity = serializers.IntegerField(read_only=True)
    item_total_price = serializers.SerializerMethodField()

    class Meta:
        model = ShopOrderItem
        fields = ('product', 'unit_price', 'quantity', 'item_total_price')

    def get_item_total_price(self, obj):
        return obj.quantity * obj.unit_price


class ShopOrderSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    shop_id = serializers.IntegerField(source='shop.id', read_only=True)
    shop_order_id = serializers.IntegerField(source='id', read_only=True)
    shop = serializers.CharField(source='shop.name', read_only=True)
    status_from_shop = serializers.CharField(source='status', read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    suborder_total_amount = serializers.DecimalField(
                                source='total_amount',
                                max_digits=12,
                                decimal_places=2,
                                read_only=True
                            )
    items = ShopOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = ShopOrder
        fields = (
            'order_id',
            'shop_order_id',
            'shop_id',
            'shop',
            'status_from_shop',
            'updated_at',
            'suborder_total_amount',
            'items',
        )


class OrderSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source='id', read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    # updated_at = serializers.DateTimeField(read_only=True)
    order_total_amount = serializers.DecimalField(
        source='total_amount',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    suborders = ShopOrderSerializer(
        source='shop_orders',
        many=True,
        read_only=True
    )

    class Meta:
        model = Order
        fields = (
            'order_id',
            'status',
            'created_at',
            # 'updated_at',
            'order_total_amount',
            'suborders',
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


class ShopOrderStatusSerializer(serializers.Serializer):
    """
    Для смены статуса конкретного ShopOrder.
    """
    status = serializers.ChoiceField(choices=ShopOrder.STATUS_CHOICES)
