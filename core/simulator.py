"""
FloodWatch Kerala — Automatic Water Level & Rainfall Simulator
Runs in a background thread. No external API, no sync button needed.
Each station has its own behaviour pattern (rising, falling, stable, fluctuating).
"""
import threading
import random
import math
import time
import logging

logger = logging.getLogger(__name__)

_simulator_started = False
_lock = threading.Lock()


# ── Per-station behaviour config ──────────────────────────────────────────────
# Keys match location_name substrings (case-insensitive)
# trend: 'rising' | 'falling' | 'stable' | 'wave'
# speed: meters per tick (tick = 15s)
STATION_PROFILES = [
    {'match': 'Bharathapuzha',  'trend': 'rising',     'speed': 0.06, 'rain_base': 38, 'rain_amp': 22},
    {'match': 'Pampa River',    'trend': 'wave',        'speed': 0.04, 'rain_base': 30, 'rain_amp': 18},
    {'match': 'Periyar River',  'trend': 'rising',      'speed': 0.03, 'rain_base': 25, 'rain_amp': 15},
    {'match': 'Kabani River',   'trend': 'rising',      'speed': 0.05, 'rain_base': 42, 'rain_amp': 20},
    {'match': 'Mananthavady',   'trend': 'rising',      'speed': 0.04, 'rain_base': 44, 'rain_amp': 18},
    {'match': 'Kallada',        'trend': 'stable',      'speed': 0.01, 'rain_base': 12, 'rain_amp':  8},
    {'match': 'Achankovil',     'trend': 'stable',      'speed': 0.01, 'rain_base': 10, 'rain_amp':  6},
    {'match': 'Valapattanam',   'trend': 'wave',        'speed': 0.03, 'rain_base': 20, 'rain_amp': 12},
    {'match': 'Meenachil',      'trend': 'falling',     'speed': 0.02, 'rain_base': 15, 'rain_amp':  8},
    {'match': 'Muvattupuzha',   'trend': 'wave',        'speed': 0.03, 'rain_base': 22, 'rain_amp': 14},
    {'match': 'Pamba at Alla',  'trend': 'rising',      'speed': 0.03, 'rain_base': 28, 'rain_amp': 12},
    {'match': 'Chaliyar',       'trend': 'falling',     'speed': 0.02, 'rain_base': 18, 'rain_amp': 10},
    {'match': 'Kallayi',        'trend': 'stable',      'speed': 0.01, 'rain_base':  8, 'rain_amp':  5},
    {'match': 'Karyangode',     'trend': 'stable',      'speed': 0.01, 'rain_base':  9, 'rain_amp':  6},
]

DEFAULT_PROFILE = {'trend': 'wave', 'speed': 0.02, 'rain_base': 15, 'rain_amp': 10}


def _get_profile(location_name):
    low = location_name.lower()
    for p in STATION_PROFILES:
        if p['match'].lower() in low:
            return p
    return DEFAULT_PROFILE


def _compute_new_level(current, danger, warning, profile, tick):
    """Return new water level based on trend."""
    trend = profile['trend']
    speed = profile['speed']
    min_level = warning * 0.2
    max_level = danger * 1.05  # can slightly exceed danger

    if trend == 'rising':
        # Rises until near max, then bounces back
        if current >= max_level:
            delta = -speed * random.uniform(0.5, 1.5)
        elif current >= danger * 0.95:
            delta = speed * random.uniform(-0.3, 0.8)   # slow near top
        else:
            delta = speed * random.uniform(0.4, 1.4)
    elif trend == 'falling':
        if current <= min_level:
            delta = speed * random.uniform(0.3, 1.0)
        else:
            delta = -speed * random.uniform(0.5, 1.5)
    elif trend == 'stable':
        delta = random.uniform(-speed, speed)
    else:  # wave — sinusoidal oscillation
        phase = (tick * speed * 3) % (2 * math.pi)
        delta = math.sin(phase) * speed * random.uniform(0.6, 1.4)

    new = current + delta
    return round(max(min_level, min(new, max_level)), 2)


def _compute_rainfall(profile, tick, water_level, warning_level):
    """Simulate rainfall (mm/hr) — higher when water is high."""
    base = profile['rain_base']
    amp  = profile['rain_amp']
    # Sinusoidal pattern with some noise
    phase = (tick * 0.15) % (2 * math.pi)
    value = base + amp * math.sin(phase) + random.uniform(-4, 4)
    # Scale up if water level is above warning
    if water_level > warning_level:
        factor = 1 + (water_level - warning_level) / warning_level * 0.5
        value *= factor
    return round(max(0, value), 1)


def _compute_accuracy(rainfall_mm, trend):
    """Rainfall accuracy % — higher when rain is steady, lower when extreme."""
    if rainfall_mm < 5:
        base = random.uniform(88, 97)
    elif rainfall_mm < 20:
        base = random.uniform(82, 94)
    elif rainfall_mm < 40:
        base = random.uniform(74, 88)
    else:
        base = random.uniform(60, 78)   # extreme rain = less accurate
    return round(base, 1)


def _weather_desc(rainfall_mm):
    if rainfall_mm < 2.5:  return 'Clear skies'
    if rainfall_mm < 7.5:  return 'Light rain'
    if rainfall_mm < 15:   return 'Moderate rain'
    if rainfall_mm < 30:   return 'Heavy rain'
    if rainfall_mm < 50:   return 'Very heavy rain'
    return 'Extremely heavy rain'


def _temperature(rainfall_mm):
    base = 28 - rainfall_mm * 0.12
    return round(max(18, min(36, base + random.uniform(-1, 1))), 1)


def _humidity(rainfall_mm):
    base = 60 + rainfall_mm * 0.6
    return round(max(40, min(99, base + random.uniform(-3, 3))), 1)


def _simulator_loop():
    """Main loop — runs every 15 seconds, updates all WaterLevel records."""
    from django.utils import timezone
    from core.models import WaterLevel

    tick = 0
    logger.info('🌊 FloodWatch Simulator started.')

    while True:
        try:
            stations = list(WaterLevel.objects.all())
            for station in stations:
                profile = _get_profile(station.location_name)

                new_level   = _compute_new_level(
                    station.current_level_meters,
                    station.danger_level_meters,
                    station.warning_level_meters,
                    profile, tick
                )
                rainfall    = _compute_rainfall(profile, tick, new_level, station.warning_level_meters)
                accuracy    = _compute_accuracy(rainfall, profile['trend'])
                description = _weather_desc(rainfall)
                temp        = _temperature(rainfall)
                humidity    = _humidity(rainfall)

                station.current_level_meters  = new_level
                station.rainfall_mm           = rainfall
                station.rainfall_accuracy_pct = accuracy
                station.weather_description   = description
                station.temperature_c         = temp
                station.humidity_pct          = humidity
                station.api_last_synced       = timezone.now()
                station.save()   # triggers status auto-computation in model.save()

            tick += 1
        except Exception as exc:
            logger.warning(f'Simulator tick error: {exc}')

        time.sleep(15)   # update every 15 seconds


def start_simulator():
    """Call once from AppConfig.ready(). Guards against double-start."""
    global _simulator_started
    with _lock:
        if _simulator_started:
            return
        _simulator_started = True

    t = threading.Thread(target=_simulator_loop, daemon=True, name='FloodWatchSimulator')
    t.start()
    logger.info('✅ FloodWatch background simulator thread started.')
