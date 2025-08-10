from django.db.models import ProtectedError
from django.shortcuts import render
from rest_framework import permissions, status, generics, viewsets
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from users.models import DeliveryContact
from users.serializers import RegistrationSerializer, EmailTokenObtainPairSerializer, DeliveryContactSerializer
from users.tasks import send_welcome_email


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

        # 3 Генерируем токен и отправляем приветственный email
        send_welcome_email.delay(user.id)
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
    возвращает refresh и access токены
    """
    serializer_class = EmailTokenObtainPairSerializer


class DeliveryContactViewSet(viewsets.ModelViewSet):
    """
    Список и создание контактов доставки для текущего пользователя.

    list:
        GET /api/contacts/ — возвращает все сохраненные контакты.
    create:
        POST /api/contacts/ — создает новый контакт.
    delete:
        DELETE /api/contacts/{pk}/ — удаляет контакт (если не привязан к заказам).
    """
    serializer_class = DeliveryContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # возвращаем только свои контакты
        return DeliveryContact.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # сохраняем user автоматически
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        contact = self.get_object()
        try:
            contact.delete()
        except ProtectedError:
            return Response(
                {'detail': 'Невозможно удалить контакт — он уже использован в заказе'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {'detail': 'Контакт успешно удален'},
            status=status.HTTP_204_NO_CONTENT
        )
