import yaml
from django.core.management import BaseCommand, CommandError

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

        
