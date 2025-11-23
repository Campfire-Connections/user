# user/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from user.models import User


class ProfileUserFieldsMixin(forms.ModelForm):
    """Shared username/email/name fields for profile ModelForms."""

    user_username = forms.CharField(max_length=150)
    user_email = forms.EmailField()
    user_first_name = forms.CharField(max_length=30)
    user_last_name = forms.CharField(max_length=30)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and getattr(self.instance, "user_id", None):
            user = self.instance.user
            self.fields["user_username"].initial = user.username
            self.fields["user_email"].initial = user.email
            self.fields["user_first_name"].initial = user.first_name
            self.fields["user_last_name"].initial = user.last_name

    def clean_user_username(self):
        username = self.cleaned_data["user_username"]
        existing = User.objects.filter(username=username)
        # Allow keeping the same username on update
        if self.instance and getattr(self.instance, "user_id", None):
            existing = existing.exclude(pk=self.instance.user_id)
        if existing.exists():
            raise ValidationError("Username is already taken.")
        return username

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = getattr(profile, "user", None)
        user_id = getattr(profile, "user_id", None)
        if not user_id:
            # Create a new user if one does not exist yet
            user = User(
                user_type=self._infer_user_type(profile),
                is_active=True,
                username=self.cleaned_data["user_username"],
                email=self.cleaned_data["user_email"],
                first_name=self.cleaned_data["user_first_name"],
                last_name=self.cleaned_data["user_last_name"],
            )
            profile.user = user
        elif not user:
            # Shouldn't happen, but guard anyway
            user = User.objects.get(id=user_id)
            profile.user = user

        user.username = self.cleaned_data["user_username"]
        user.email = self.cleaned_data["user_email"]
        user.first_name = self.cleaned_data["user_first_name"]
        user.last_name = self.cleaned_data["user_last_name"]
        if commit:
            user.save()
            profile.save()
        return profile

    def _infer_user_type(self, profile):
        """Best-effort user_type based on the profile class name."""
        name = profile.__class__.__name__.lower()
        if "leader" in name:
            return User.UserType.LEADER
        if "attendee" in name:
            return User.UserType.ATTENDEE
        if "faculty" in name:
            return User.UserType.FACULTY
        return User.UserType.OTHER


class RegistrationForm(UserCreationForm):
    """A custom user registration form for creating new user accounts.

    Extends the UserCreationForm to include an email field and customize the user creation process.

    Attributes:
        email: An email field with custom widget attributes.

    Methods:
        save: Overrides the default save method to set the user as inactive initially.
    """

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Email"}
        ),
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def save(self, commit=True):
        """
        Save the user instance with an inactive status for email activation.
        """
        user = super().save(commit=False)
        user.is_active = False
        if commit:
            user.save()
        return user


class AdminUserForm(forms.ModelForm):
    """Lightweight admin-facing form for portal user edits."""

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "user_type",
            "is_admin",
            "is_active",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "user_type": forms.Select(attrs={"class": "form-control"}),
            "is_admin": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
