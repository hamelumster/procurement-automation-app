from rest_framework import serializers

from orders.models import CartItem, Cart


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    shop = serializers.CharField(source='product.shop.name', read_only=True)
    unit_price = serializers.DecimalField(
        source='unit_price',
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
    items = CartItemSerializer(many=True, source='cartitem_set', read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ('items', 'total')

    def get_total(self, cart):
        return sum(item.unit_price * item.quantity for item in cart.cartitem_set.all())
