from rest_framework import serializers

from products.models import Product


class ProductSerializer(serializers.ModelSerializer):
    supplier = serializers.CharField(source='shop.name', read_only=True)
    category = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'name',
            'description',
            'supplier',
            'category',
            'characteristics',
            'price',
            'quantity',
        ]
