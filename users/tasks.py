from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string

from orders.models import Order

User = get_user_model()

@shared_task
def send_welcome_email(user_id):
    """
    Отправить новому пользователю письмо с приветствием после успешной регистрации.
    """
    user = User.objects.get(id=user_id)
    subject = 'Добро пожаловать!'
    context = {'user': user}
    text_body = render_to_string('emails/welcome.txt', context)
    html_body = render_to_string('emails/welcome.html', context)

    send_mail(
        subject,
        text_body,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_body,
        fail_silently=False,
    )

@shared_task
def send_order_confirmation_email(order_id):
    """
    Отправить письмо-подтверждение клиенту и админу
    """
    order = Order.objects.select_related('delivery_contact', 'user').prefetch_related('shop_orders__items').get(pk=order_id)
    # Формируем текст письма
    subject = f"Ваш заказ #{order.id} принят"
    context = {'order': order}
    text_body = render_to_string('emails/order_confirmation.txt', context)
    html_body = render_to_string('emails/order_confirmation.html', context)

    recipient = [order.delivery_contact.email]
    # можно добавить администратора:
    # admin_email = [settings.DEFAULT_FROM_EMAIL]

    # Отправляем клиенту
    send_mail(
        subject,
        text_body,
        settings.DEFAULT_FROM_EMAIL,
        recipient,
        html_message=html_body,
        fail_silently=False,
    )

    # отправляем администратору
    # send_mail(
    #     f"[ADMIN] Новый заказ #{order.id}",
    #     text_body,
    #     settings.DEFAULT_FROM_EMAIL,
    #     html_message=html_body,
    #     fail_silently=False,
    # )
