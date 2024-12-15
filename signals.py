# user/signals.py

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.db.models.signals import post_save
from django.dispatch import receiver

from user.models import User

@receiver(post_save, sender=User)
def send_activation_email(sender, instance, created, **kwargs):
    if created and not instance.is_active:
        subject = "Activate Your Account"
        uid = urlsafe_base64_encode(force_bytes(instance.pk))
        token = default_token_generator.make_token(instance)
        activation_link = reverse("activate", kwargs={"uidb64": uid, "token": token})
        activation_url = f"http://yourdomain.com{activation_link}"

        message = render_to_string("email/activation_email.html", {
            "user": instance,
            "activation_url": activation_url,
        })
        send_mail(subject, message, "admin@yourdomain.com", [instance.email])

