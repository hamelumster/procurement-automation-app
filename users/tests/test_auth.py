from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AuthTests(APITestCase):

    def test_register(self):
        url_register = reverse('auth_register')
        data = {
            'first_name': 'Jack',
            'last_name': 'Sparrow',
            'email': 'black_pearl@example.com',
            'password': '12345678'
        }

        # Регистрация
        response = self.client.post(url_register, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        # Пользователь создан
        user = User.objects.get(email=data['email'])
        self.assertTrue(user.check_password(data['password']))

        