from django.contrib.auth import get_user_model
from rest_framework import serializers

from users.models import UserProfile

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password')

    def validate_email(self, value):
        """Проверка уникальности email"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Пользователь с таким email уже зарегистрирован')
        return value

    def create(self, validated_data):
        # Создаем пользователя и хешируем пароль
        user = User(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            username=validated_data['email'],
        )
        user.set_password(validated_data['password'])
        user.save()

        # Создаем профиль клиента
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)

        return user