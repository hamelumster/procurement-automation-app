from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string

User = get_user_model()

@shared_task
def send_welcome_email(user_id):
    """
    Отправить новому пользователю письмо с приветствием после успешной регистрации.
    """
    user = User.objects.get(id=user_id)
    subject = 'Добро пожаловать!'
    context = {'user': user}
    text_body = render_to_string('welcome_email.txt', context)
    html_body = render_to_string('welcome_email.html', context)

    send_mail(
        subject,
        text_body,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_body,
        fail_silently=False,
    )
