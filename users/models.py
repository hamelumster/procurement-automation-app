import uuid

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
    @property
    def is_client(self):
        return self.role == self.ROLE_CLIENT

    @property
    def is_supplier(self):
        return self.role == self.ROLE_SUPPLIER

    def __str__(self):
        return f"{self.user.email} ({self.get_role_display()})"


class SupplierProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                related_name='supplier_profile')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class DeliveryContact(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delivery_contact'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=100)
    house = models.CharField(max_length=100)
    building = models.CharField(max_length=100, blank=True, null=True)
    apartment = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}, {self.city}, {self.street}, {self.house}"

class EmailVerification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='email_verification'
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"Email verification for {self.user.email}"

