import yaml
from django.core.management import BaseCommand, CommandError

from products.models import Category, Product
from shops.models import Shop
from users.models import SupplierProfile


class Command(BaseCommand):
    help="Импортирует товары из yaml файла"
    def add_arguments(self, parser):
        parser.add_argument(
            'yaml_file',
            type=str,
            help='Путь к yaml-файлу с данными'
        )
        parser.add_argument(
            '--supplier-email',
            type=str,
            required=True,
            help='Email поставщика'
        )

    def handle(self, *args, **options):
        yaml_path = options['yaml_file']
        supplier_email = options['supplier_email']

        # 1 Загрузить yaml файл
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            raise CommandError(f'Файл {yaml_path} не найден')
        except yaml.YAMLError as e:
            raise CommandError(f'Ошибка: {e}')

        # 2 Найти поставщика по email
        try:
            supplier = SupplierProfile.objects.get(user__email=supplier_email)
        except SupplierProfile.DoesNotExist:
            raise CommandError(f'Поставщик с email {supplier_email} не найден')

        # 3 Создать или получить магазин по имени из yaml файла
        shop_name = data.get('shop')
        if not shop_name:
            raise CommandError('Название магазина не указано в yaml файле')
        shop, created = Shop.objects.get_or_create(
            name=shop_name,
            supplier=supplier,
            defaults={'description': shop_name, 'is_active': True}
        )
        self.stdout.write(f"Магазин {shop_name} {'создан' if created else 'найден'}")

        # 4 Импорт категорий
        created_cats = updated_cats = 0
        for cat_data in data.get('categories', []):
            obj, was_created = Category.objects.update_or_create(
                external_id=cat_data['id'],
                defaults={'name': cat_data['name']}
            )
            if was_created:
                created_cats += 1
            else:
                updated_cats += 1
        self.stdout.write(f"Создано {created_cats} категорий, обновлено {updated_cats}")

        # 5 Импорт товаров
        created_products = updated_products = 0
        for item in data.get('goods', []):
            try:
                category = Category.objects.get(external_id=item['category'])
            except Category.DoesNotExist:
                self.stdout.write(f"Категория {item['category']} не найдена")
                continue

            product, was_created = Product.objects.update_or_create(
                external_id=item['id'],
                defaults={
                    'category': category,
                    'shop': shop,
                    'model': item['model'],
                    'name': item['name'],
                    'description': item.get('description', ''),
                    'characteristics': item.get('characteristics', {}),
                    'price': item['price'],
                    'price_rrc': item['price_rrc'],
                    'quantity': item['quantity'],
                }
            )
            if was_created:
                created_products += 1
            else:
                updated_products += 1
        self.stdout.write(f"Создано {created_products} товаров, обновлено {updated_products}")
        
