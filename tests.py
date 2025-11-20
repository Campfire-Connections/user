from django.test import TestCase

from user.models import User


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
