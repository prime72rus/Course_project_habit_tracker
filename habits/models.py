from django.core.exceptions import ValidationError, PermissionDenied
from django.db import models


class Habit(models.Model):
    """
    Модель привычки
    """
    PERIODICITY_CHOICES = [
        (1, "Ежедневно"),
        (2, "Раз в 2 дня"),
        (3, "Раз в 3 дня"),
        (4, "Раз в 4 дня"),
        (5, "Раз в 5 дней"),
        (6, "Раз в 6 дней"),
        (7, "Раз в неделю"),
    ]

    owner = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="habits",
        verbose_name="Владелец",
    )
    place = models.CharField(
        max_length=255,
        verbose_name="Место выполнения",
    )
    time_action = models.TimeField(
        verbose_name="Время выполнения",
    )
    action = models.CharField(
        max_length=255,
        verbose_name="Выполняемое действие",
    )
    is_pleasant_habit = models.BooleanField(
        default=False,
        verbose_name="Признак приятной привычки",
    )
    related_habit = models.ForeignKey(
        "Habit",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="habits",
        verbose_name="Связанная привычка",
    )
    periodicity = models.PositiveSmallIntegerField(
        choices=PERIODICITY_CHOICES,
        default=1,
        verbose_name="Периодичность (дни)"
    )
    reward = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Вознаграждение",
    )
    duration = models.PositiveSmallIntegerField(
        verbose_name="Время на выполнение (секунды)",
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name="Признак публичности",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Признак активности привычки"
    )

    class Meta:
        verbose_name = "Привычка",
        verbose_name_plural = "Привычки"

    def clean(self):
        """
        Валидация данных при сохранении экземпляра сущности
        """
        if self.duration > 120:
            raise ValidationError(
                {"duration":
                    "Время выполнения не должно превышать 120 секунд"}
            )

        if self.periodicity > 7:
            raise ValidationError(
                {"periodicity":
                    "Нельзя выполнять привычку реже, чем 1 раз в 7 дней"}
            )

        if self.is_pleasant_habit:
            if self.reward or self.related_habit:
                raise ValidationError(
                    "Приятная привычка не может иметь вознаграждения"
                    " или связанной привычки"
                )

        if self.related_habit and not self.related_habit.is_pleasant:
            raise ValidationError(
                {"related_habit": "Связанная привычка должна быть приятной"}
            )

        if self.related_habit and self.reward:
            raise ValidationError(
                "Можно указать либо связанную привычку,"
                " либо вознаграждение, но не оба"
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.action
