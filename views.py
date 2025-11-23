# user/views.py
""" Users Related Views. """

import logging
from django.contrib import messages
from django.contrib.auth import login as _login, logout as _logout, authenticate
from django.contrib.auth.views import LogoutView as _LogoutView, LoginView as _LoginView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.views.generic import TemplateView, DetailView

from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse, NoReverseMatch
from django.utils.http import urlsafe_base64_decode

from django.views.generic.edit import FormView
from django.utils.translation import gettext_lazy as _

from django.template import loader, TemplateDoesNotExist
from django.contrib.contenttypes.models import ContentType

from core.views.base import BaseDashboardView, BaseTableListView
from user.tables import AdminUserTable

from facility.forms.faculty import FacultyForm
from faction.forms.attendee import AttendeeProfileForm
from faction.forms.leader import LeaderProfileForm
from facility.models.faculty import FacultyProfile
from faction.models.leader import LeaderProfile
from faction.models.attendee import AttendeeProfile

from .forms import RegistrationForm
from .models import User

logger = logging.getLogger(__name__)


def activate_user(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except Exception:
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your account has been activated successfully.")
        return redirect("login")

    messages.error(request, "The activation link is invalid or has expired.")
    return redirect("register")


class LoginView(_LoginView):
    template_name = "auth/signin.html"
    form_class = AuthenticationForm
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        _login(self.request, form.get_user())
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

    profile_map = {
        "Attendee": (AttendeeProfileForm, AttendeeProfile),
        "Leader": (LeaderProfileForm, LeaderProfile),
        "Faculty": (FacultyForm, FacultyProfile),
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        POST = self.request.POST or None

        context["attendee_form"] = AttendeeProfileForm(POST)
        context["leader_form"] = LeaderProfileForm(POST)
        context["faculty_form"] = FacultyForm(POST)

        # If AddressForm is later implemented, add here:
        # context["address_form"] = AddressForm(POST)

        return context

    def form_valid(self, form):
        user = User.objects.create_user(
            username=form.cleaned_data["username"],
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
        )

        role = form.cleaned_data.get("user_type")
        ProfileFormClass, ProfileModel = self.profile_map.get(role)

        profile_form = ProfileFormClass(self.request.POST)

        # Address form commented out until implemented
        # address_form = AddressForm(self.request.POST)

        if profile_form.is_valid():
            profile = self.save_profile(user, profile_form)
            return super().form_valid(form)

        for field, errors in profile_form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")

        return self.form_invalid(form)

    def save_profile(self, user, form):
        profile = form.save(commit=False)
        profile.user = user
        profile.save()
        return profile


class LogoutView(_LogoutView):
    """Logout the user and redirect to home."""
    next_page = reverse_lazy("home")


class DashboardView(LoginRequiredMixin, BaseDashboardView):
    """
    Redirect authenticated users to their appropriate dashboard.
    """

    dashboard_redirects = {
        "attendee": "attendees:dashboard",
        "leader": "leaders:dashboard",
        "faculty": "facultys:dashboard",
        "admin": "admin_portal_dashboard",
    }

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        user = request.user

        if user.is_superuser:
            return redirect(reverse_lazy("admin_portal_dashboard"))

        redirect_url = self.get_dashboard_redirect_url(user)
        if redirect_url:
            return redirect(redirect_url)

        logger.warning(f"No dashboard found for user type: {user.user_type}")
        return redirect(reverse_lazy("home"))

    def get_dashboard_redirect_url(self, user):
        override = getattr(user, "dashboard_route", None)
        if callable(override):
            override = override()
        if override:
            return reverse_lazy(override)

        role = getattr(user, "user_type", "").lower()
        return reverse_lazy(self.dashboard_redirects.get(role, "home"))


class AdminDashboardView(LoginRequiredMixin, BaseDashboardView):
    template_name = "admin/dashboard.html"
    portal_key = "admin"

    def _safe_url(self, name, kwargs=None, default="#"):
        try:
            return reverse(name, kwargs=kwargs or {})
        except NoReverseMatch:
            return default

    def get_admin_actions_widget(self, _definition):
        return {
            "actions": [
                {"label": "Open Django Admin", "url": self._safe_url("admin:index"), "icon": "fas fa-shield-alt"},
                {"label": "Manage Users", "url": self._safe_url("admin_user_list"), "icon": "fas fa-users-cog"},
                {"label": "Manage Organizations", "url": self._safe_url("organization_index"), "icon": "fas fa-sitemap"},
                {"label": "Manage Facilities", "url": self._safe_url("facilities:index"), "icon": "fas fa-campground"},
                {"label": "Manage Factions", "url": self._safe_url("factions:index"), "icon": "fas fa-users"},
                {"label": "Manage Courses", "url": self._safe_url("courses:index"), "icon": "fas fa-book-reader"},
                {"label": "Reports", "url": self._safe_url("reports:list_user_reports"), "icon": "fas fa-chart-bar"},
            ]
        }

    def get_admin_resources_widget(self, _definition):
        return {
            "items": [
                {"title": "Docs", "description": "Project documentation", "url": "https://docs.djangoproject.com/"},
                {"title": "Manage Users", "description": "View all users", "url": self._safe_url("admin_user_list")},
                {"title": "Manage Facilities", "description": "Facility directory", "url": self._safe_url("facilities:index")},
                {"title": "Manage Factions", "description": "Faction hierarchy", "url": self._safe_url("factions:index")},
                {"title": "Manage Courses", "description": "Course admin", "url": self._safe_url("courses:index")},
            ]
        }

    def get_admin_users_widget(self, _definition):
        return {
            "table_class": AdminUserTable,
            "queryset": User.objects.order_by("username"),
        }


class AdminUserListView(LoginRequiredMixin, BaseTableListView):
    model = User
    table_class = AdminUserTable
    template_name = "admin/user_list.html"
    context_object_name = "users"
    paginate_by = 25

    def get_queryset(self):
        return User.objects.order_by("username")


class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = "user/settings.html"


class AdminUserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "admin/user_detail.html"
    slug_field = "username"
    slug_url_kwarg = "username"
    context_object_name = "user_obj"


class PublicUserDetailView(AdminUserDetailView):
    """Public-facing version of user detail."""
    pass


class AdminUserEditRedirectView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return redirect(reverse("admin_user_detail", kwargs={"username": self.object.username}))


class AdminUserDeleteRedirectView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return redirect(reverse("admin_user_detail", kwargs={"username": self.object.username}))
