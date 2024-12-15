# user/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm

from user.models import User


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
