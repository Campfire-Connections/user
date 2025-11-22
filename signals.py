# user/signals.py

from threading import Thread

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from user.models import User


@receiver(post_save, sender=User)
def send_activation_email(sender, instance, created, **kwargs):
    if not created or instance.is_active or not instance.email:
        return

    base_url = getattr(settings, "SITE_BASE_URL", "")
    if not base_url and settings.ALLOWED_HOSTS:
        base_url = f"https://{settings.ALLOWED_HOSTS[0]}"
    if not base_url:
        base_url = "http://localhost:8000"
    base_url = base_url.rstrip("/")

    uid = urlsafe_base64_encode(force_bytes(instance.pk))
    token = default_token_generator.make_token(instance)
    activation_link = reverse("activate", kwargs={"uidb64": uid, "token": token})
    activation_url = f"{base_url}{activation_link}"

    message = render_to_string(
        "email/activation_email.html",
        {
            "user": instance,
            "activation_url": activation_url,
        },
    )

    def _deliver():
        send_mail(
            subject="Activate Your Account",
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[instance.email],
            fail_silently=True,
        )

    Thread(target=_deliver, daemon=True).start()
