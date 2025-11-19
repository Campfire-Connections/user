# user/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm

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

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.username = self.cleaned_data["user_username"]
        user.email = self.cleaned_data["user_email"]
        user.first_name = self.cleaned_data["user_first_name"]
        user.last_name = self.cleaned_data["user_last_name"]
        if commit:
            user.save()
            profile.save()
        return profile


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
