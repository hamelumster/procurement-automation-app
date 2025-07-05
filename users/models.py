from django.conf import settings
from django.db import models

class UserProfile(models.Model):

    ROLE_CLIENT = 'client'
    ROLE_SUPPLIER = 'supplier'
    ROLE_CHOICES = [
        (ROLE_CLIENT, 'Клиент'),
        (ROLE_SUPPLIER, 'Поставщик'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                related_name='profile')
    role = models.CharField(max_length=20,
                            choices=ROLE_CHOICES,
                            default=ROLE_CLIENT)
    phone = models.CharField(max_length=20,
                             blank=True,
                             null=True,
                             help_text='Номер телефона пользователя')
    created_at = models.DateTimeField(auto_now_add=True,
                                      help_text='Дата и время создания профиля')
    updated_at = models.DateTimeField(auto_now=True,
                                      help_text='Дата и время последнего обновления профиля')

    def __str__(self):
        return f"{self.user.email} ({self.get_role_display()})"

