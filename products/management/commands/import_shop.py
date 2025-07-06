from django.core.management import BaseCommand


class Command(BaseCommand):
    help="Импортирует товары из yaml файла"
    def add_arguments(self, parser):
        parser.add_argument('yaml_file',
                            type=str,
                            help='Путь к yaml-файлу с данными'
        )
