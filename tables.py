import django_tables2 as tables
from django.contrib.auth import get_user_model
from django.urls import reverse

from core.tables.base import BaseTable

User = get_user_model()


class AdminUserTable(BaseTable):
    available_actions = ["show", "edit", "delete"]
    url_namespace = "admin"
    username = tables.Column()
    email = tables.Column()
    user_type = tables.Column(verbose_name="Role")
    is_admin = tables.BooleanColumn(verbose_name="Portal Admin")
    is_active = tables.BooleanColumn()

    class Meta:
        model = User
        template_name = "django_tables2/bootstrap4.html"
        fields = ("username", "email", "user_type", "is_admin", "is_active")
        attrs = {"class": "table table-striped table-sm"}

    def get_url(self, action, record=None, context=None):
        """
        Use slug/username driven routes for detail/edit/delete.
        """
        if not record:
            return super().get_url(action, record=record, context=context)

        if action == "show":
            profile = None
            if hasattr(record, "get_profile"):
                try:
                    profile = record.get_profile()
                except Exception:
                    profile = None
            if profile and hasattr(profile, "get_absolute_url"):
                return profile.get_absolute_url()
            return reverse("user_detail", kwargs={"username": record.username})
        if action == "edit":
            return reverse("admin_user_edit", kwargs={"username": record.username})
        if action == "delete":
            return reverse("admin_user_delete", kwargs={"username": record.username})
        return super().get_url(action, record=record, context=context)
