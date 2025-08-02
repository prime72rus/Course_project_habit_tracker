from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated

from users.models import User
from users.permissions import IsSuperUser, IsAdminUser, IsOwner
from users.serializers import UserAdminSerializer, UserSerializer


class UserListAPIView(ListAPIView):
    serializer_class = UserAdminSerializer
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsSuperUser | IsAdminUser]


class UserRetrieveAPIView(RetrieveAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsSuperUser | IsAdminUser | IsOwner]

    def get_serializer_class(self):
        if self.request.user.is_superuser:
            return UserAdminSerializer
        return UserSerializer


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
    permission_classes = [IsAuthenticated, IsSuperUser | IsAdminUser | IsOwner]

    def get_serializer_class(self):
        if self.request.user.is_superuser:
            return UserAdminSerializer
        return UserSerializer

    def perform_update(self, serializer):
        if "password" in serializer.validated_data:
            user = serializer.save()
            user.set_password(serializer.validated_data["password"])
            user.save()
        else:
            serializer.save()


class UserDestroyAPIView(DestroyAPIView):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsSuperUser | IsAdminUser]
