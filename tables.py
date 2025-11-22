import django_tables2 as tables
from django.contrib.auth import get_user_model

from core.tables.base import BaseTable

User = get_user_model()


class AdminUserTable(BaseTable):
    available_actions = []
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
