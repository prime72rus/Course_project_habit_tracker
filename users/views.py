from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import (
    CreateAPIView, DestroyAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView
)

from users.models import User
from users.serializers import UserAdminSerializer, UserSerializer


class UserListAPIView(ListAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get_queryset(self):
        if self.request.user.is_superuser:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    def get_serializer_class(self):
        if self.request.user.is_superuser:
            return UserAdminSerializer
        return UserSerializer


class UserRetrieveAPIView(RetrieveAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get_object(self):
        user = super().get_object()
        request_user = self.request.user
        if request_user.is_superuser:
            return user
        if user != request_user:
            raise PermissionDenied(
                "Вы можете просматривать только свой профиль"
            )
        return user


class UserCreateAPIView(CreateAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def perform_create(self, serializer):
        user = serializer.save(is_active=True)
        user.set_password(user.password)
        user.save()

    def get_serializer_class(self):
        if self.request.user.is_superuser:
            return UserAdminSerializer
        return UserSerializer


class UserUpdateAPIView(UpdateAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get_object(self):
        user = super().get_object()
        request_user = self.request.user
        if request_user.is_superuser:
            return user
        if user != request_user:
            raise PermissionDenied(
                "Вы можете редактировать только свой профиль"
            )
        return user

    def perform_update(self, serializer):
        if "password" in serializer.validated_data:
            user = serializer.save()
            user.set_password(serializer.validated_data["password"])
            user.save()
        else:
            serializer.save()


class UserDestroyAPIView(DestroyAPIView):
    queryset = User.objects.all()

    def get_object(self):
        user = super().get_object()
        request_user = self.request.user
        if request_user.is_superuser:
            return user
        if user != request_user:
            raise PermissionDenied("Вы можете удалить только свой профиль")
        return user
