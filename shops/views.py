import yaml
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import permissions, status, generics
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from shops.models import Shop
from shops.serializers import ShopAvialableSerializer
from shops.services.shop_export import ShopExportService
from shops.services.shop_import import ShopImportService
from users.models import SupplierProfile


class SupplierFeedUpload(APIView):
    """
    Позволяет поставщику загрузить YAML-файл с товарами
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        # 1 найти профиль поставщика
        try:
            supplier = request.user.supplier_profile
        except SupplierProfile.DoesNotExist:
            return Response({'detail': 'Поставщик не найден'}, status=status.HTTP_400_BAD_REQUEST)

        # 2 загрузить и распарсить файл
        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'detail': 'Файл не загружен'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            raw = uploaded.read().decode('utf-8')
            shop_data = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            return Response({'detail': f'Ошибка при чтении YAML-файла: {e}'}, status=status.HTTP_400_BAD_REQUEST)

        # 3 импортируем товары
        service = ShopImportService(supplier, shop_data)
        result = service.run()

        return Response(result, status=status.HTTP_200_OK)


class ShopToggleAvailability(generics.UpdateAPIView):
    """
    Позволяет поставщику включать и отключать приём заказов для конкретного магазина.

    Только аутентифицированные пользователи с профилем SupplierProfile
    могут менять флаг is_active у своих магазинов. Запросы на изменение чужих
    магазинов запрещены.
    """
    queryset = Shop.objects.all()
    serializer_class = ShopAvialableSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        supplier = self.request.user.supplier_profile
        shop_pk = self.kwargs['shop_id']
        return get_object_or_404(Shop, pk=shop_pk, supplier=supplier)


class ShopExportView(APIView):
    """
    GET /api/shops/{shop_id}/export/
    - сгенерировать и скачать YAML-файл (прайс) заданного магазина.
    Доступно только его владельцу (supplier_profile).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, shop_id):
        # 1 Проверяем, что магазин принадлежит текущему поставщику
        shop = get_object_or_404(
            Shop,
            pk=shop_id,
            supplier=request.user.supplier_profile
        )

        # 2 Генерируем YAML-файл
        yaml_str = ShopExportService(shop).run()

        # 3 Формируем имя файла
        slug = slugify(shop.name)
        timestamp = timezone.localtime().strftime('%Y%m%d')
        filename = f'{slug}_{timestamp}.yaml'

        # 4 Возвращаем HttpResponse с заголовком для скачивания
        return HttpResponse(
            yaml_str,
            content_type='application/x-yaml',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
