from django.conf import settings
from django.core.mail import send_mail

from django_rq import job


@job
def send_email(email: str, subject: str, message: str) -> None:
    send_mail(
        subject,
        message,
        settings.FROM_EMAIL,
        [email],
        fail_silently=False,
    )
