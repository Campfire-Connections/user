# user/views.py
""" Users Related Views. """

import logging
from django.contrib import messages
from django.contrib.auth import login as _login, logout as _logout
from django.contrib.auth.views import LogoutView as _LogoutView, LoginView as _LoginView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django.template import loader, TemplateDoesNotExist
from django.views.generic.edit import FormView
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _


# from address.forms import AddressForm
from facility.models.faculty import FacultyProfile
from faction.forms.attendee import AttendeeProfileForm
from faction.forms.leader import LeaderProfileForm
from facility.forms.faculty import FacultyForm
from faction.models.leader import LeaderProfile
from faction.models.attendee import AttendeeProfile
from core.views.base import BaseDashboardView


from .forms import RegistrationForm
from .models import User


logger = logging.getLogger(__name__)


def activate_user(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your account has been activated successfully.")
        return redirect("login")
    else:
        messages.error(request, "The activation link is invalid or has expired.")
        return redirect("register")


class LoginView(_LoginView):
    template_name = "auth/signin.html"
    form_class = AuthenticationForm
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        user = form.get_user()
        _login(self.request, user)
        return super().form_valid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)


class RegisterView(FormView):
    template_name = "signup.html"
    form_class = RegistrationForm
    success_url = reverse_lazy("success_url")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["attendee_form"] = AttendeeProfileForm(self.request.POST or None)
        context["leader_form"] = LeaderProfileForm(self.request.POST or None)
        context["faculty_form"] = FacultyProfileForm(self.request.POST or None)
        context["address_form"] = AddressForm(self.request.POST or None)
        return context

    def form_valid(self, form):
        user = User.objects.create_user(
            username=form.cleaned_data["username"],
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
        )
        user_type = form.cleaned_data["user_type"]

        if user_type == "Attendee":
            profile_form = AttendeeProfileForm(self.request.POST)
            ProfileModel = AttendeeProfile
        elif user_type == "Leader":
            profile_form = LeaderProfileForm(self.request.POST)
            ProfileModel = LeaderProfile
        elif user_type == "Faculty":
            profile_form = FacultyProfileForm(self.request.POST)
            ProfileModel = FacultyProfile

        address_form = AddressForm(self.request.POST)
        if profile_form.is_valid() and address_form.is_valid():
            profile = self.save_profile(user, profile_form)
            self.save_address(address_form, profile, ProfileModel)
            return super().form_valid(form)
        else:
            for field, errors in profile_form.errors.items():
                for error in errors:
                    messages.error(self.request, f"{field}: {error}")
            for field, errors in address_form.errors.items():
                for error in errors:
                    messages.error(self.request, f"{field}: {error}")
            return self.form_invalid(form)

    def save_profile(self, user, form):
        profile = form.save(commit=False)
        profile.user = user
        profile.save()
        return profile

    def save_address(self, form, profile, ProfileModel):
        address = form.save(commit=False)
        content_type = ContentType.objects.get_for_model(ProfileModel)
        address.content_type = content_type
        address.object_id = profile.pk
        address.save()
        return address


class LogoutView(_LogoutView):
    """Logout the user and redirect to the home page."""

    next_page = reverse_lazy("home")


class DashboardView(LoginRequiredMixin, BaseDashboardView):
    """
    Main dashboard view that redirects users to their respective role-based dashboards.
    """

    # Role-based dashboard mappings
    dashboard_redirects = {
        "attendee": "attendees:dashboard",
        "leader": "leaders:dashboard",
        "faculty": "facultys:dashboard",
    }

    def dispatch(self, request, *args, **kwargs):
        """
        Redirect users to their respective dashboards based on their role or permissions.
        """
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        user = request.user

        # Superuser redirection
        if user.is_superuser:
            return redirect(reverse_lazy("admin:index"))

        # Redirect based on user type
        dashboard_url = self.get_dashboard_redirect_url(user)
        if dashboard_url:
            return redirect(dashboard_url)

        # Default fallback if no role-specific dashboard is found
        logger.warning(f"No dashboard found for user type: {user.user_type}")
        return redirect(reverse_lazy("home"))

    def get_dashboard_redirect_url(self, user):
        """
        Determine the appropriate dashboard URL for the user.
        """
        override_route = getattr(user, "dashboard_route", None)
        if callable(override_route):
            override_route = override_route()
        if override_route:
            return reverse_lazy(override_route)

        user_type = getattr(user, "user_type", "").lower()

        if user_type in self.dashboard_redirects:
            return reverse_lazy(self.dashboard_redirects[user_type])

        return None


class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = "user/settings.html"
