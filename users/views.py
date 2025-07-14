from django.shortcuts import render
from rest_framework import permissions

from users.serializers import RegistrationSerializer


class RegisterAPIView():
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        # 1 Проверяем данные
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 2 Создаем пользователя + профиль
        user = serializer.save()

        

