from contextlib import contextmanager

from django.db.models.signals import post_save
from django.test import TestCase
from django.urls import reverse

from user.models import (
    User,
    create_profile as create_profile_signal,
    save_profile as save_profile_signal,
    update_profile_slug as update_profile_slug_signal,
)


class UserModelTests(TestCase):
    def test_full_name_is_combined(self):
        user = User.objects.create_user(
            username="full.name",
            password="testpass123",
            user_type=User.UserType.ADMIN,
            first_name="Full",
            last_name="Name",
        )
        self.assertEqual(user.get_full_name(), "Full Name")


@contextmanager
def mute_profile_signals():
    receivers = [
        create_profile_signal,
        save_profile_signal,
        update_profile_slug_signal,
    ]
    for receiver in receivers:
        post_save.disconnect(receiver, sender=User)
    try:
        yield
    finally:
        for receiver in receivers:
            post_save.connect(receiver, sender=User)


class DashboardRouteTests(TestCase):
    def setUp(self):
        self.dashboard_url = reverse("dashboard")

    def test_requires_login(self):
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    def test_leader_redirects_to_portal_dashboard(self):
        with mute_profile_signals():
            leader = User.objects.create_user(
                username="leader.route",
                password="pass1234",
                user_type=User.UserType.LEADER,
            )

        self.client.force_login(leader)
        response = self.client.get(self.dashboard_url)
        self.assertRedirects(
            response,
            reverse("leaders:dashboard"),
            fetch_redirect_response=False,
        )
