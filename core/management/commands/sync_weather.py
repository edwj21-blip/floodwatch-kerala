"""
Management command: sync real weather/rainfall data and update water levels.

Usage:
    python manage.py sync_weather            # run once
    python manage.py sync_weather --loop 300 # loop every 300 seconds (5 min)
"""
import time
from django.core.management.base import BaseCommand
from core.services.weather_service import sync_all_water_levels


class Command(BaseCommand):
    help = 'Fetch live weather data from OpenWeatherMap and update water levels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loop', type=int, default=0,
            help='If > 0, repeat every N seconds continuously'
        )

    def handle(self, *args, **options):
        loop_sec = options['loop']
        self.stdout.write(self.style.SUCCESS('🌧  FloodWatch Weather Sync Starting...'))

        if loop_sec > 0:
            self.stdout.write(f'   Running every {loop_sec}s. Press Ctrl+C to stop.\n')
            try:
                while True:
                    self._run_sync()
                    time.sleep(loop_sec)
            except KeyboardInterrupt:
                self.stdout.write('\nStopped.')
        else:
            self._run_sync()

    def _run_sync(self):
        result = sync_all_water_levels()
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Synced {result['updated']} locations | "
                f"Alerts created: {result['alerts_created']} | "
                f"Errors: {result['errors']}"
            )
        )
