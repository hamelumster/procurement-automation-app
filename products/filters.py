import django_filters

from products.models import Product


class ProductFilter(django_filters.FilterSet):
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    supplier = django_filters.CharFilter(field_name='shop__id')
    category = django_filters.CharFilter(field_name='category__external_id')

    class Meta:
        model = Product
        fields = ['supplier', 'category', 'price_min', 'price_max']