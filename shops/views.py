import yaml
from django.shortcuts import render
from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

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
