from django.db import models


class Product(models.Model):
    supplier = models.ForeignKey(
        'users.SupplierProfile',
        on_delete=models.CASCADE,
        related_name='products'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    characteristics = models.JSONField(
        blank=True,
        null=True,
        help_text='Характеристики товара в виде словаря'
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.supplier.user.email})"
    
