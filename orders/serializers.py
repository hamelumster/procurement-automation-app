from rest_framework import serializers

from orders.models import CartItem, Cart
from products.models import Product
from users.models import DeliveryContact


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    shop = serializers.CharField(source='product.shop.name', read_only=True)
    unit_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True)
    total_price = serializers.SerializerMethodField()

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

    def get_total_price(self, obj):
        return obj.quantity * obj.unit_price


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ('items', 'total')

    def get_total(self, cart):
        return sum(item.unit_price * item.quantity for item in cart.items.all())


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
