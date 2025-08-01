from rest_framework import serializers

from shops.models import Shop


class ShopAvialableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('id', 'is_active')