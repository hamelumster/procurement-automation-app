from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from orders.models import Cart, CartItem
from orders.serializers import CartSerializer, AddCartItemSerializer
from products.models import Product


class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        GET /api/cart/
        -> возвращает текущую корзину пользователя
        """
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(methods=['post'], detail=False, url_path='items')
    def add_item(self, request):
        """
        POST /api/cart/items/
        { "product_id": 1, "quantity": 2 }
        -> добавляет товар в корзину (или увеличивает его кол-во)
        """
        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = get_object_or_404(Product, pk=serializer.validated_data['product_id'])
        qty = serializer.validated_data['quantity']
        cart, _ = Cart.objects.get_or_create(user=request.user)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': qty, 'unit_price': product.price}
        )
        if not created:
            item.quantity += qty
            item.save(update_fields=['quantity'])

        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)
