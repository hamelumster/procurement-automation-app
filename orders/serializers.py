from rest_framework import serializers

from orders.models import CartItem


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


