from django.core.exceptions import ObjectDoesNotExist

from products.models import Category, Product
from shops.models import Shop
from users.models import SupplierProfile


class ShopImportService:
    def __init__(self, supplier: SupplierProfile, shop_data: dict):
        self.supplier = supplier
        self.shop_data = shop_data
        self.created_cats = self.updated_cats = 0
        self.created_products = self.updated_products = 0

    def _get_or_create_shop(self):
        name = self.shop_data.get('shop')
        if not name:
            raise ValueError('Название магазина не указано в yaml файле')
        shop, created = Shop.objects.get_or_create(
            name=name,
            supplier=self.supplier,
            defaults={'description': name, 'is_active': True}
        )
        return shop

    def _import_categories(self):
        for cat in self.shop_data.get('categories', []):
            obj, created = Category.objects.get_or_create(
                external_id=cat.get('id'),
                defaults={'name': cat.get('name')}
            )
            if created:
                self.created_cats += 1
            else:
                self.updated_cats += 1

    def _import_products(self, shop):
        for item in self.shop_data.get('goods', []):
            try:
                category = Category.objects.get(external_id=item.get('category_id'))
            except ObjectDoesNotExist:
                continue
            product, created = Product.objects.update_or_create(
                external_id=item.get('id'),
                defaults={
                    'category': category,
                    'shop': shop,
                    'model': item['model'],
                    'name': item['name'],
                    'description': item.get('description', ''),
                    'characteristics': item.get('parameters', {}),
                    'price': item['price'],
                    'price_rrc': item['price_rrc'],
                    'quantity': item['quantity'],
                }
            )
            if created:
                self.created_products += 1
            else:
                self.updated_products += 1

    def run(self):
        shop = self._get_or_create_shop()
        self._import_categories()
        self._import_products(shop)
        return {
            'created_categories': self.created_cats,
            'updated_categories': self.updated_cats,
            'created_products': self.created_products,
            'updated_products': self.updated_products,
        }
