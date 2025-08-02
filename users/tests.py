from django.test import TestCase, RequestFactory
from django.urls import reverse

from habits.models import Habit
from users.models import User
from rest_framework import status
from rest_framework.test import APITestCase, APIClient, APIRequestFactory

from users.permissions import IsOwner
from users.serializers import UserSerializer, UserAdminSerializer


class UserTests(APITestCase):
    """Тесты для API пользователей"""

    def setUp(self):
        """Инициализация тестовых данных"""
        self.client = APIClient()
        # Создаем тестового администратора
        self.admin = User.objects.create(
            email="admin@example.com",
            password="adminpass",
            first_name="Admin",
            last_name="User",
            is_superuser=True,
            is_staff=True,
        )
        # Создаем обычного пользователя
        self.user = User.objects.create(
            email="user@example.com",
            password="userpass",
            first_name="Regular",
            last_name="User"
        )
        # Создаем персонал (staff)
        self.staff = User.objects.create(
            email="staff@example.com",
            password="staffpass",
            first_name="Staff",
            last_name="User",
            is_staff=True
        )

    # --- REGISTRATION TESTS ---
    def test_user_registration(self):
        """Тест регистрации нового пользователя

        Проверяет:
        - Успешное создание пользователя (код 201)
        - Увеличение количества пользователей в БД
        - Наличие нового пользователя в БД
        """
        url = reverse("users:user_register")
        data = {
            "email": "newuser@example.com",
            "password": "newpass123",
            "first_name": "New",
            "last_name": "User"
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 4)
        self.assertTrue(
            User.objects.filter(email="newuser@example.com").exists())

    # --- USER LIST TESTS ---
    def test_user_list_as_admin(self):
        """Тест получения списка пользователей администратором

        Проверяет:
        - Успешный запрос (код 200)
        - Администратор видит всех пользователей (включая других админов и персонал)
        """
        self.client.force_authenticate(user=self.admin)
        url = reverse("users:users_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # admin + user + staff

    def test_user_list_as_staff(self):
        """Тест получения списка пользователей персоналом

        Проверяет:
        - Успешный запрос (код 200)
        - Персонал не видит суперпользователей
        """
        self.client.force_authenticate(user=self.staff)
        url = reverse("users:users_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Staff should not see superusers
        self.assertEqual(len(response.data), 2)  # user + staff

    # --- USER DETAIL TESTS ---
    def test_user_detail_as_owner(self):
        """Тест просмотра профиля владельцем

        Проверяет:
        - Успешный запрос (код 200)
        - Корректность возвращаемых данных
        """
        self.client.force_authenticate(user=self.user)
        url = reverse("users:user_detail", args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "user@example.com")

    def test_user_detail_as_admin(self):
        """Тест просмотра профиля администратором

        Проверяет:
        - Администратор может просматривать любой профиль
        """
        self.client.force_authenticate(user=self.admin)
        url = reverse("users:user_detail", args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # --- USER UPDATE TESTS ---
    def test_user_update_as_owner(self):
        """Тест обновления профиля владельцем

        Проверяет:
        - Успешное обновление данных (код 200)
        - Изменение данных в БД
        """
        self.client.force_authenticate(user=self.user)
        url = reverse("users:user_update", args=[self.user.id])
        data = {
            "first_name": "Updated",
            "last_name": "Name",
            "phone": "+1234567890"
        }
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")

    # --- USER DELETE TESTS ---
    def test_user_delete_as_admin(self):
        """Тест удаления пользователя администратором

        Проверяет:
        - Успешное удаление (код 204)
        - Отсутствие пользователя в БД после удаления
        """
        self.client.force_authenticate(user=self.admin)
        url = reverse("users:user_delete", args=[self.user.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.user.id).exists())

    def test_user_delete_as_staff(self):
        """Тест удаления пользователя персоналом

        Проверяет:
        - Персонал может удалять пользователей
        """
        self.client.force_authenticate(user=self.staff)
        url = reverse("users:user_delete", args=[self.user.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.user.id).exists())

    def test_user_cannot_delete_self(self):
        """Тест запрета удаления собственного аккаунта

        Проверяет:
        - Обычный пользователь не может удалить себя (код 403)
        """
        self.client.force_authenticate(user=self.user)
        url = reverse("users:user_delete", args=[self.user.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- PERMISSION TESTS ---
    def test_admin_can_see_all_users(self):
        """Тест прав администратора на просмотр всех пользователей

        Проверяет:
        - Администратор видит всех пользователей без ограничений
        """
        self.client.force_authenticate(user=self.admin)
        url = reverse("users:users_list")
        response = self.client.get(url)
        self.assertEqual(len(response.data), 3)  # All users

    def test_staff_cannot_see_superusers(self):
        """Тест ограничений персонала на просмотр суперпользователей

        Проверяет:
        - Персонал не видит суперпользователей в списке
        """
        self.client.force_authenticate(user=self.staff)
        url = reverse("users:users_list")
        response = self.client.get(url)
        user_ids = [user["id"] for user in response.data]
        self.assertNotIn(self.admin.id, user_ids)

    def test_regular_user_cannot_access_user_list(self):
        """Тест запрета доступа обычных пользователей к списку пользователей

        Проверяет:
        - Обычный пользователь получает отказ в доступе (код 403)
        """
        self.client.force_authenticate(user=self.user)
        url = reverse("users:users_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_string_representation(self):
        """Тест строкового представления привычки"""
        self.assertEqual(str(self.admin), "admin@example.com")


class IsOwnerPermissionTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create(
            email="test@example.com",
            password="testpass"
        )
        self.other_user = User.objects.create(
            email="other@example.com",
            password="otherpass"
        )
        self.permission = IsOwner()

        # Создаем тестовый объект Habit с владельцем
        self.habit = Habit.objects.create(
            owner=self.user,
            place="Дома",
            time_action="08:00:00",
            action="Чтение",
            duration=30
        )

    def test_permission_with_user_object_owner(self):
        """Тест разрешения для владельца (User объект)"""
        request = self.factory.get("/")
        request.user = self.user
        self.assertTrue(
            self.permission.has_object_permission(request, None, self.user))

    def test_permission_with_user_object_not_owner(self):
        """Тест запрета для не владельца (User объект)"""
        request = self.factory.get("/")
        request.user = self.other_user
        self.assertFalse(
            self.permission.has_object_permission(request, None, self.user))

    def test_permission_with_owned_object(self):
        """Тест разрешения для объекта с владельцем"""
        request = self.factory.get("/")
        request.user = self.user
        self.assertTrue(
            self.permission.has_object_permission(request, None, self.habit))

    def test_permission_with_not_owned_object(self):
        """Тест запрета для объекта с другим владельцем"""
        request = self.factory.get("/")
        request.user = self.other_user
        self.assertFalse(
            self.permission.has_object_permission(request, None, self.habit))

    def test_permission_with_invalid_object_type(self):
        """Тест для неподдерживаемого типа объекта (проверка return False)"""

        class SomeOtherClass:
            pass

        request = self.factory.get("/")
        request.user = self.user
        some_object = SomeOtherClass()

        # Проверяем, что для неподдерживаемого типа объекта возвращается False
        self.assertFalse(
            self.permission.has_object_permission(request, None, some_object))


class UserSerializerTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.serializer_class = UserSerializer

    def test_get_extra_kwargs_no_request(self):
        """Тест без request в контексте"""
        serializer = self.serializer_class(context={})
        result = serializer.get_extra_kwargs()
        self.assertEqual(result, {})

    def test_get_extra_kwargs_with_request_get(self):
        """Тест с GET-запросом (должен добавить только write_only для password)"""
        request = self.factory.get("/")
        serializer = self.serializer_class(context={"request": request})
        result = serializer.get_extra_kwargs()

        expected = {
            "password": {"write_only": True}
        }
        self.assertEqual(result, expected)

    def test_get_extra_kwargs_with_request_put(self):
        """Тест с PUT-запросом (должен добавить write_only)"""
        request = self.factory.put("/")
        serializer = self.serializer_class(context={"request": request})
        result = serializer.get_extra_kwargs()

        expected = {
            "password": {"write_only": True},
        }
        self.assertEqual(result, expected)

    def test_get_extra_kwargs_with_request_patch(self):
        """Тест с PATCH-запросом (должен добавить write_only и read_only поля)"""
        request = self.factory.patch("/")
        serializer = self.serializer_class(context={"request": request})
        result = serializer.get_extra_kwargs()

        expected = {
            "password": {"write_only": True},
        }
        self.assertEqual(result, expected)
