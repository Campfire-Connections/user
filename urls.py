# user/urls.py

from django.urls import path

from facility.views.faculty import RegisterFacultyView

from . import views

urlpatterns = [
    path("login", views.LoginView.as_view(), name="login"),
    path("signin", views.LoginView.as_view(), name="signin"),
    path("register", views.RegisterView.as_view(), name="register"),
    path("register/faculty/", RegisterFacultyView.as_view(), name="register_faculty"),
    path("activate/<uidb64>/<token>/", views.activate_user, name="activate"),
    path("signup", views.RegisterView.as_view(), name="signup"),
    path("profile/", views.DashboardView.as_view(), name="profile"),
    #path("dashboard", views.DashboardView.as_view(), name="dashboard"),
    path("admin-portal/", views.AdminDashboardView.as_view(), name="admin_portal_dashboard"),
    path("admin/users/", views.AdminUserListView.as_view(), name="admin_user_list"),
    path("logout", views.LogoutView.as_view(), name="logout"),
    path("signout", views.LogoutView.as_view(), name="signout"),
    path("account", views.SettingsView.as_view(), name="account_settings"),
]
