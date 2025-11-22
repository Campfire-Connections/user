from contextlib import contextmanager

from django.db.models.signals import post_save
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

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

    def test_attendee_redirects(self):
        with mute_profile_signals():
            attendee = User.objects.create_user(
                username="attendee.route",
                password="pass1234",
                user_type=User.UserType.ATTENDEE,
            )
        self.client.force_login(attendee)
        response = self.client.get(self.dashboard_url)
        self.assertRedirects(
            response,
            reverse("attendees:dashboard"),
            fetch_redirect_response=False,
        )

    def test_faculty_redirects(self):
        with mute_profile_signals():
            faculty = User.objects.create_user(
                username="faculty.route",
                password="pass1234",
                user_type=User.UserType.FACULTY,
            )
        self.client.force_login(faculty)
        response = self.client.get(self.dashboard_url)
        self.assertRedirects(
            response,
            reverse("facultys:dashboard"),
            fetch_redirect_response=False,
        )

    def test_admin_without_superuser_falls_back_to_home(self):
        with mute_profile_signals():
            admin_user = User.objects.create_user(
                username="admin.route",
                password="pass1234",
                user_type=User.UserType.ADMIN,
            )
        self.client.force_login(admin_user)
        response = self.client.get(self.dashboard_url)
        self.assertRedirects(
            response,
            reverse("home"),
            fetch_redirect_response=False,
        )

    def test_superuser_redirects_to_admin(self):
        with mute_profile_signals():
            superuser = User.objects.create_superuser(
                username="super.route",
                email="super@example.com",
                password="pass1234",
            )
        self.client.force_login(superuser)
        response = self.client.get(self.dashboard_url)
        self.assertRedirects(
            response,
            reverse("admin:index"),
            fetch_redirect_response=False,
        )

    def test_dashboard_route_override_takes_precedence(self):
        original_property = getattr(User, "dashboard_route", None)

        def _override(self):
            return (
                "reports:list_user_reports"
                if self.username == "leader.with.override"
                else None
            )

        User.dashboard_route = property(_override)

        def _restore():
            if original_property is None:
                delattr(User, "dashboard_route")
            else:
                setattr(User, "dashboard_route", original_property)

        self.addCleanup(_restore)
        with mute_profile_signals():
            leader = User.objects.create_user(
                username="leader.with.override",
                password="pass1234",
                user_type=User.UserType.LEADER,
            )
        self.client.force_login(leader)
        response = self.client.get(self.dashboard_url)
        self.assertRedirects(
            response,
            reverse("reports:list_user_reports"),
            fetch_redirect_response=False,
        )


class ActivateUserTests(TestCase):
    def setUp(self):
        with mute_profile_signals():
            self.user = User.objects.create_user(
                username="activate.me",
                password="pass12345",
                user_type=User.UserType.ADMIN,
                is_active=False,
            )

    def test_valid_token_activates_user(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        response = self.client.get(reverse("activate", args=[uid, token]))
        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_invalid_token_redirects_to_register(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        response = self.client.get(reverse("activate", args=[uid, "invalid-token"]))
        self.assertRedirects(
            response, reverse("register"), fetch_redirect_response=False
        )
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
