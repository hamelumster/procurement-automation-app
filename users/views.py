from django.shortcuts import render
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from users.serializers import RegistrationSerializer, EmailTokenObtainPairSerializer


class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        """
        POST /api/auth/register/
        {
            "first_name": "Jack",
            "last_name": "Sparrow",
            "email": "black_pearl@example.com",
            "password": "12345678"
        }
        -> {
        "refresh": <jwt_refresh_token>
        "access": <jwt_access_token>
        }
        """
        # 1 Проверяем данные
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 2 Создаем пользователя + профиль
        user = serializer.save()

        # 3 Генерируем токен
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        # 4 Возвращаем токен
        return Response(
            {
                'refresh': str(refresh),
                'access': str(access)
            },
            status=status.HTTP_201_CREATED
        )


class EmailTokenObtainPairView(TokenObtainPairView):
    """
    Логин по email + password;
    возвращает refresh и access
    """
    serializer_class = EmailTokenObtainPairSerializer