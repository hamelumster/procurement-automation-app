from shops.models import Shop


class ShopExportService:
    """
    Собирает для заданного магазина товары,
    и возвращает валидный YAML-документ в виде строки.
    """
    def __init__(self, shop: Shop):
        self.shop = Shop

    def assembly_categories(self):
        pass

    def assembly_products(self):
        pass

    def run(self):
        pass