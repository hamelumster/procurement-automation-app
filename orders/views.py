from collections import defaultdict

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from orders.models import Cart, CartItem, Order, ShopOrder, ShopOrderItem
from orders.serializers import (CartSerializer, AddCartItemSerializer, RemoveCartItemSerializer,
                                OrderSerializer, ShopOrderStatusSerializer, ShopOrderSerializer)
from products.models import Product
from users.models import DeliveryContact
from users.tasks import send_order_confirmation_email


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
        serializer = AddCartItemSerializer(data=request.data, context={'request': request})
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
        GET  /api/orders/ — список всех заказов клиента (или всех для admin).
    retrieve:
        GET  /api/orders/{pk}/ — детали одного заказа.
    confirm:
        POST /api/orders/confirm/ — оформить корзину в Order + ShopOrder.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)

    @action(detail=False, methods=['post'], url_path='confirm')
    def confirm(self, request):
        """
        POST /api/orders/confirm/
        {
          "cart_id": <int>,
          "contact_id": <int>
        }
        — создаёт Order и разбивает его на ShopOrder для каждого магазина.
        """
        cart_id = request.data.get('cart_id')
        contact_id = request.data.get('contact_id')

        cart = get_object_or_404(Cart, pk=cart_id, user=request.user)
        contact = get_object_or_404(DeliveryContact,
                                    pk=contact_id,
                                    user=request.user)

        if not cart.items.exists():
            return Response({'detail': 'Корзина пуста'},
                            status=status.HTTP_400_BAD_REQUEST)

        # 1) заводим общий Order
        order = Order.objects.create(user=request.user,
                                     delivery_contact=contact,
                                     status=Order.STATUS_NEW,
                                     total_amount=0)

        # 2) группируем CartItem по shop
        by_shop = defaultdict(list)
        for ci in cart.items.select_related('product__shop'):
            by_shop[ci.product.shop].append(ci)

        # 3) по каждой группе создаём ShopOrder + ShopOrderItem’ы
        for shop, items in by_shop.items():
            so = ShopOrder.objects.create(
                order=order,
                shop=shop,
                status=ShopOrder.STATUS_NEW,
                total_amount=0
            )
            for ci in items:
                ShopOrderItem.objects.create(
                    shop_order=so,
                    product=ci.product,
                    quantity=ci.quantity,
                    unit_price=ci.unit_price
                )
            so.calculate_total()

        # 4) пересчитываем итоговую сумму общего Order
        order.calculate_total()

        # 4.1) "Списываем" товар со склада
        for so in order.shop_orders.all():
            for item in so.items.all():
                Product.objects.filter(pk=item.product_id).update(
                    quantity=F('quantity') - item.quantity
                )

        # 5) Отправляем email с подтверждением заказа
        send_order_confirmation_email.delay(order.id)

        # 5) очищаем корзину
        cart.items.all().delete()

        return Response(OrderSerializer(order).data,
                        status=status.HTTP_201_CREATED)

    @action(methods=['post'], detail=True, url_path='cancel')
    def cancel(self, request, pk=None):
        """
        POST /api/orders/{pk}/cancel/
        Отменить заказ может только автор заказа или админ.
        """
        order = self.get_object()

        # только клиент‑автор или is_staff
        if not (request.user.is_staff or order.user == request.user):
            return Response({'detail': 'Недостаточно прав'},
                            status=status.HTTP_403_FORBIDDEN)

        # если уже отменён или завершён
        if order.status in (Order.STATUS_CANCELLED, Order.STATUS_COMPLETED):
            return Response({'detail': 'Нельзя отменить'},
                            status=status.HTTP_400_BAD_REQUEST)

        # ставим статус cancelled
        order.cancel()

        # отменяем все связанные ShopOrder
        ShopOrder.objects.filter(order=order).update(status=ShopOrder.STATUS_CANCELLED)

        return Response(self.get_serializer(order).data,
                        status=status.HTTP_200_OK)


class ShopOrderViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       viewsets.GenericViewSet):
    """
    list:
        GET  /api/shop-orders/ — список подзаказов магазина.
    retrieve:
        GET  /api/shop-orders/{pk}/ — детали одного подзаказа.
    process:
        PATCH /api/shop-orders/{pk}/process/ — сменить статус подзаказа.
    """
    serializer_class = ShopOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # админ видит все
        if user.is_staff:
            return ShopOrder.objects.all()

        # поставщики — только свои ShopOrder’ы
        try:
            sp = user.supplier_profile
        except ObjectDoesNotExist:
            return ShopOrder.objects.none()

        return ShopOrder.objects.filter(shop__supplier=sp)

    @action(detail=True, methods=['patch'], url_path='process')
    def process(self, request, pk=None):
        """
        PATCH /api/shop-orders/{pk}/process/
        { "status": "<new_status>" }
        — смена статуса этого ShopOrder.
        """
        shop_order = self.get_object()

        parent_order = shop_order.order
        if parent_order.status in (parent_order.STATUS_CANCELLED,
                                   parent_order.STATUS_COMPLETED):
            return Response(
                {'detail': 'Нельзя менять статус подзаказа — заказ уже закрыт.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверка прав
        profile = request.user.supplier_profile
        if shop_order.shop.supplier != profile and not request.user.is_staff:
            return Response({'detail': 'Недостаточно прав'},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = ShopOrderStatusSerializer(
            data=request.data,
            context={'shop_order': shop_order}
        )
        serializer.is_valid(raise_exception=True)

        shop_order.status = serializer.validated_data['status']
        shop_order.save(update_fields=['status'])

        return Response(self.get_serializer(shop_order).data,
                        status=status.HTTP_200_OK)
