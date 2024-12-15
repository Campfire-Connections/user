# user/models.py

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.conf import settings
from django.utils.text import slugify


from address.models import AddressField
from facility.managers.faculty import FacultyManager
from faction.managers.attendee import AttendeeManager
from faction.managers.leader import LeaderManager
from enrollment.models.enrollment import Enrollment


class User(AbstractUser):
    """Custom User Model."""

    class UserType(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        ORGANIZATION_FACULTY = "ORGANIZATION_FACULTY", "Organization Faculty"
        FACILITY_FACULTY = "FACILITY_FACULTY", "Facility Faculty"
        FACULTY = "FACULTY", "Faculty"
        LEADER = "LEADER", "Leader"
        ATTENDEE = "ATTENDEE", "Attendee"
        OTHER = "OTHER", "Other"

    user_type = models.CharField(max_length=50, choices=UserType.choices)
    is_admin = models.BooleanField(default=False)
    is_new_user = models.BooleanField(default=True)

    # Default manager for general queries
    objects = UserManager()

    # Specialized managers
    faculty_manager = FacultyManager()
    attendee_manager = AttendeeManager()
    leader_manager = LeaderManager()

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_profile(self):
        if self.user_type == User.UserType.ATTENDEE:
            return getattr(self, "attendeeprofile_profile", None)
        elif self.user_type == User.UserType.LEADER:
            return getattr(self, "leaderprofile_profile", None)
        elif self.user_type == User.UserType.FACULTY:
            return getattr(self, "facultyprofile_profile", None)
        return None

    def get_enrollments(self):
        return Enrollment.objects.filter(user=self)


class BaseUserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(class)s_profile",  # Dynamic related_name
    )
    address = AddressField(
        blank=True,
        null=True,
        related_name="%(class)s_profile",  # Avoid conflict
    )
    organization = models.ForeignKey(
        "organization.Organization",
        on_delete=models.CASCADE,
        related_name="%(class)s_profile",  # Avoid conflict
    )
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    def generate_slug(self):
        if self.user.first_name and self.user.last_name:
            return slugify(f"{self.user.first_name} {self.user.last_name}")
        return slugify(self.user.username)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_slug()
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class AdminProfile(BaseUserProfile):
    class Meta:
        abstract = True


# Corrected signals
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == "FACULTY":
            FacultyProfile.objects.create(user=instance)
        elif instance.user_type == "ATTENDEE":
            AttendeeProfile.objects.create(user=instance)
        elif instance.user_type == "LEADER":
            LeaderProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    profile = instance.get_profile()
    if profile:
        profile.save()


@receiver(post_save, sender=User)
def update_profile_slug(sender, instance, **kwargs):
    profile = instance.get_profile()
    if profile:
        # Regenerate the slug in case the first_name or last_name changes
        profile.slug = profile.generate_slug()
        profile.save()
