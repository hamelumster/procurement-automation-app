from products.models import Category
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



