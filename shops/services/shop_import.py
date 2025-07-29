from users.models import SupplierProfile


class ShopImportService:
    def __init__(self, supplier: SupplierProfile, shop_data: dict):
        self.supplier = supplier
        self.shop_data = shop_data
        self.created_cats = self.updated_cats = 0
        self.created_products = self.updated_products = 0