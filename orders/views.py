from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from orders.models import Cart, CartItem, Order, OrderItem
from orders.serializers import CartSerializer, AddCartItemSerializer, RemoveCartItemSerializer
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

    @action(methods=['delete'], detail=False, url_path=r'items/(?P<product_id>[^/.]+)')
    def remove_item(self, request, product_id=None):
        """
        DELETE /api/cart/items/{product_id}/

        Body (JSON, необязательно):
            { "quantity": <сколько убрать> }

        Логика:
          - если quantity не передан или quantity >= текущего количества —
            полностью удаляем CartItem
          - иначе уменьшаем item.quantity на указанное число
        """
        data = {'product_id': product_id}
        if isinstance(request.data, dict) and 'quantity' in request.data:
            data['quantity'] = request.data['quantity']

        serializer = RemoveCartItemSerializer(data={**request.data, 'product_id': product_id})
        serializer.is_valid(raise_exception=True)
        qty_to_remove = serializer.validated_data.get('quantity')

        cart = get_object_or_404(Cart, user=request.user)
        item = get_object_or_404(
            CartItem,
            cart=cart,
            product_id=product_id
        )

        if qty_to_remove is None or qty_to_remove >= item.quantity:
            item.delete()
        else:
            item.quantity -= qty_to_remove
            item.save(update_fields=['quantity'])

        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class OrderViewSet(viewsets.GenericViewSet):
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated]

    @action(methods=['post'], detail=False, url_path='confirm')
    def confirm(self, request):
        # 1 Получаем корзину
        cart, _ = Cart.objects.get_or_create(user=request.user)
        if not cart.items.exists():
            return Response({'detail': 'Корзина пуста'}, status=status.HTTP_400_BAD_REQUEST)

        # 2 Создаем заказ
        order = Order.objects.create(
            user=request.user,
            status=Order.STATUS_NEW,
            total_amount=0
        )

        # 3 Переносим из CartItem -> OrderItem
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price
            )

        # 4 Пересчитываем общую сумму
        order.calculate_total()

        # 5 Очищаем корзину
        cart.items.all().delete()

        # 6 Здесь будет отправка email

