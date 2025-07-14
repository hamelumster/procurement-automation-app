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

        # Логин (получение токенов)
        url_token = reverse('token_obtain_pair')
        response_2 = self.client.post(url_token, {'username': data['email'], 'password': data['password']}, format='json')
        self.assertEqual(response_2.status_code, status.HTTP_200_OK)
        self.assertIn('access', response_2.data)
        self.assertIn('refresh', response_2.data)

        # Refresh токен
        url_token_refresh = reverse('token_refresh')
        response_3 = self.client.post(url_token_refresh, {'refresh': response_2.data['refresh']}, format='json')
        self.assertEqual(response_3.status_code, status.HTTP_200_OK)
        self.assertIn('access', response_3.data)