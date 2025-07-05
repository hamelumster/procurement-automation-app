from django.db import models

class Shop(models.Model):
    supplier = models.ForeignKey(
        'users.SupplierProfile',
        on_delete=models.CASCADE,
        related_name='shops',
        help_text='Поставщик'
    )
    name = models.CharField(
        max_length=255,
        help_text='Название магазина'
    )
    description = models.TextField(
        help_text='Описание магазина',
        blank=False,
        null=False
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Принимает ли магазин заказы'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Дата и время создания магазина'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Дата и время последнего обновления магазина'
    )

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'
        ordering = ['-created_at']

    def __str__(self):
        return self.name
