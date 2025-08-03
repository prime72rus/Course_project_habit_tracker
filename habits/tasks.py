from celery import shared_task
from django.utils import timezone
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from habits.models import Habit
from habits.services import prepare_habit_message, send_tg_message


@shared_task
def send_daily_habit_reminders():
    """Ежедневная отправка напоминаний о привычках"""
    now = timezone.localtime(timezone.now())
    current_time = now.time()

    habits = Habit.objects.filter(
        time_action__hour=current_time.hour,
        time_action__minute=current_time.minute,
        is_active=True,
        owner__isnull=False,
        owner__chat_id__isnull=False,
    ).select_related("owner", "related_habit")

    for habit in habits:
        message = prepare_habit_message(habit)
        if send_tg_message(habit.owner.chat_id, message):
            print(f"Sent reminder for habit {habit.id} to {habit.owner.email}")
        else:
            print(f"Failed to send reminder for habit {habit.id}")


@shared_task
def setup_daily_reminders():
    """Настройка ежедневной проверки привычек"""

    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute="*",
        hour="*",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
    )

    PeriodicTask.objects.update_or_create(
        name="Daily habit reminders",
        defaults={
            "crontab": schedule,
            "task": "habits.tasks.send_daily_habit_reminders",
            "enabled": True,
        },
    )
