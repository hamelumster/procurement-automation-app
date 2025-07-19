from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status, mixins, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from orders.models import Cart, CartItem, Order, OrderItem
from orders.serializers import CartSerializer, AddCartItemSerializer, RemoveCartItemSerializer, ConfirmOrderSerializer, \
    OrderSerializer, OrderStatusSerializer
from products.models import Product
from users.models import DeliveryContact


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


class OrderViewSet(mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   viewsets.GenericViewSet
    ):
    """
    list:
        GET  /api/orders/        — список заказов текущего пользователя.
    retrieve:
        GET  /api/orders/{pk}/   — детали одного заказа.
    confirm:
        POST /api/orders/confirm/ — оформление заказа на основе корзины и контакта.
        POST /api/orders/{pk}/cancel/  — клиент (или админ) отменяет заказ
    process:
        PATCH /api/orders/{pk}/process/ — магазин/админ двигает статус дальше
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # возвращаем только заказы, созданные этим пользователем
        return Order.objects.filter(user=self.request.user)

    @action(methods=['post'], detail=False, url_path='confirm')
    def confirm(self, request):
        # 1 Валидируем входные данные: cart_id, contact_id
        serializer = ConfirmOrderSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        cart_id = serializer.validated_data['cart_id']
        contact_id = serializer.validated_data['contact_id']

        # 2 Получаем корзину (гарантированно принадлежит текущему пользователю)
        cart = get_object_or_404(Cart, pk=cart_id, user=request.user)
        contact = get_object_or_404(
            DeliveryContact,
            pk=contact_id,
            user=request.user
        )

        if not cart.items.exists():
            return Response(
                {'detail': 'Корзина пуста'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3 Создаем заказ
        order = Order.objects.create(
            user=request.user,
            delivery_contact=contact,
            status=Order.STATUS_NEW,
            total_amount=0
        )

        # 4 Переносим из CartItem -> OrderItem
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price
            )

        # 5 Пересчитываем общую сумму
        order.calculate_total()

        # 6 Очищаем корзину
        cart.items.all().delete()

        # 7 Здесь будет отправка email
        # ...

        out_serializer = OrderSerializer(order, context={'request': request})
        return Response(
            out_serializer.data,
            status=status.HTTP_201_CREATED
        )

    @action(methods=['post'], detail=True, url_path='cancel')
    def cancel(self, request, pk=None):
        order = self.get_object()
        profile = request.user.profile

        # Отменить может только клиент или админ
        if not (profile.is_client or request.user.is_staff):
            return Response({'detail': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)

        if order.status in (Order.STATUS_CANCELLED, Order.STATUS_COMPLETED):
            return Response({'detail': 'Нельзя отменить'}, status=status.HTTP_400_BAD_REQUEST)

        order.status = Order.STATUS_CANCELLED
        order.save(update_fields=['status'])
        return Response(self.get_serializer(order).data, status=status.HTTP_200_OK)

    @action(methods=['patch'], detail=True, url_path='process')
    def process(self, request, pk=None):
        order = self.get_object()
        profile = request.user.profile

        # Обработать может только админ или поставщик
        if not (profile.is_supplier or request.user.is_staff):
            return Response({'detail': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)

        serializer = OrderStatusSerializer(
            data=request.data,
            context={'order': order}
        )
        serializer.is_valid(raise_exception=True)

        order.status = serializer.validated_data['status']
        order.save(update_fields=['status'])

        return Response(self.get_serializer(order).data, status=status.HTTP_200_OK)