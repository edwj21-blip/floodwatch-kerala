import os
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Only start in the main process (not in migrations, shell, etc.)
        # RUN_MAIN is set by Django's autoreloader for the worker process
        is_main = os.environ.get('RUN_MAIN') == 'true' or not os.environ.get('DJANGO_SETTINGS_MODULE', '').endswith('test')
        if os.environ.get('DJANGO_SIMULATOR', '1') == '1' and is_main:
            try:
                from core.simulator import start_simulator
                start_simulator()
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f'Could not start simulator: {e}')
