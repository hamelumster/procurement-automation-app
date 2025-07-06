import yaml
from django.core.management import BaseCommand, CommandError


class Command(BaseCommand):
    help="Импортирует товары из yaml файла"
    def add_arguments(self, parser):
        parser.add_argument('yaml_file',
                            type=str,
                            help='Путь к yaml-файлу с данными'
        )

    def handle(self, *args, **options):
        yaml_path = options['yaml_file']

        # 1 Загрузить yaml файл
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            raise CommandError(f'Файл {yaml_path} не найден')
        except yaml.YAMLError as e:
            raise CommandError(f'Ошибка: {e}')
        