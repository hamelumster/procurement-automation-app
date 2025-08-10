from django.shortcuts import render

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter

from products.filters import ProductFilter
from products.models import Product
from products.serializers import ProductSerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/products/
    Поддерживается:
        - ?search=… — поиск по name и description
        - ?supplier=… — фильтр по id магазина
        - ?category=… — фильтр по внешнему id категории
        - ?price_min=… — цена >= …
        - ?price_max=… — цена <= …
        - ?ordering=… — сортировка (например price, -name)
    """
    queryset = Product.objects.select_related('shop', 'category').all()
    serializer_class = ProductSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'name', 'quantity']
    ordering = ['name']
