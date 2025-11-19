from rest_framework import serializers

from .models import User


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "email", "user_type")


class BaseProfileSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer()

    class Meta:
        fields = ("id", "slug", "user")

