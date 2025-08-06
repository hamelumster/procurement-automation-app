from collections import OrderedDict

from products.models import Category, Product
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
        queryset = Product.objects.filter(shop=self.shop).ordered_by('external_id')
        products = []
        for ps in queryset:
            products.append(OrderedDict([
                ('id', ps.external_id),
                ('category_id', ps.category.external_id),
                ('model', ps.model),
                ('name', ps.name),
                ('description', ps.description),
                ('parameters', ps.characteristics),
                ('price', ps.price),
                ('price_rrc', ps.price_rrc),
                ('quantity', ps.quantity),
            ]))
        return products

    def run(self):
        pass