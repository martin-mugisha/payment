from django.apps import AppConfig


class ConfigConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'config'

    def ready(self):
        from .signals import earnings_signals, auth_signals
        # Ensure signals are imported when the app is ready
        # This will register the signal handlers defined in config/signals.py   