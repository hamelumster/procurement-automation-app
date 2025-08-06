from collections import OrderedDict

from products.models import Category
from shops.models import Shop


class ShopExportService:
    """
    Собирает для заданного магазина товары,
    и возвращает валидный YAML-документ в виде строки.
    """
    def __init__(self, shop: Shop):
        self.shop = Shop

    def assembly_categories(self):
        queryset = Category.objects.filter(
            products__shop=self.shop
        ).distinct().order_by('external_id')
        categories = []
        for cat in queryset:
            categories.append(OrderedDict([
                ('id', cat.external_id),
                ('name', cat.name)
            ]))
        return categories

    def assembly_products(self):
        pass

    def run(self):
        pass