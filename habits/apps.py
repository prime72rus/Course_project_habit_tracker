from django.apps import AppConfig


class HabitsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "habits"

    def ready(self):
        # Инициализация периодических задач при запуске приложения
        if not hasattr(self, "already_loaded"):
            from habits.tasks import setup_daily_reminders

            setup_daily_reminders.delay()
            self.already_loaded = True
