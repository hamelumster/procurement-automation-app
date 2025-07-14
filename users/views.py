from django.shortcuts import render
from rest_framework import permissions
from rest_framework_simplejwt.tokens import RefreshToken

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

        # 3 Генерируем токен
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        

