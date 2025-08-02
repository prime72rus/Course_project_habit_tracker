from rest_framework import serializers

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "city",
            "chat_id",
            "password",
        )

    def get_extra_kwargs(self):
        extra_kwargs = super().get_extra_kwargs()
        request = self.context.get("request")
        if not request:
            return extra_kwargs

        extra_kwargs["password"] = {"write_only": True}

        if request.method in [
            "PUT",
            "PATCH",
        ]:
            extra_kwargs["email"] = {"read_only": True}
            extra_kwargs["id"] = {"read_only": True}
        return extra_kwargs


class UserAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"

    def get_extra_kwargs(self):
        extra_kwargs = super().get_extra_kwargs()
        request = self.context.get("request")

        if not request.user.is_superuser and request.method in [
            "PUT",
            "PATCH",
        ]:
            extra_kwargs["email"] = {"read_only": True}
            extra_kwargs["id"] = {"read_only": True}
        return extra_kwargs
