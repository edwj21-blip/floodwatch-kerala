"""
Weather service — fetches real rainfall data from OpenWeatherMap API
and updates WaterLevel records automatically.
"""
import urllib.request
import urllib.parse
import json
import logging
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Rainfall impact on water level (meters rise per mm of rain)
RAIN_RISE_FACTOR = 0.012   # 1 mm rain → ~1.2 cm water rise
EVAPORATION_RATE = 0.003   # natural drain per cycle (meters)

# Accuracy bands: rainfall mm → confidence %
def _rainfall_accuracy(rain_mm, humidity, description):
    """Compute rainfall accuracy % based on weather conditions."""
    base = 60.0
    if rain_mm > 50:
        base = 95.0
    elif rain_mm > 20:
        base = 88.0
    elif rain_mm > 10:
        base = 80.0
    elif rain_mm > 5:
        base = 72.0
    elif rain_mm > 0:
        base = 65.0

    # Humidity boost
    if humidity > 85:
        base = min(base + 5, 99)
    # Keyword boost
    for kw in ('heavy rain', 'thunderstorm', 'torrential', 'shower'):
        if kw in description.lower():
            base = min(base + 4, 99)
            break
    return round(base, 1)


def fetch_weather(lat, lon):
    """
    Fetch current weather from OpenWeatherMap for given coordinates.
    Returns dict with rainfall_mm, temp, humidity, description, icon or None on error.
    """
    api_key = getattr(settings, 'OPENWEATHER_API_KEY', '')
    if not api_key or api_key == 'YOUR_OPENWEATHER_API_KEY_HERE':
        logger.warning("OpenWeatherMap API key not configured — using simulated data")
        return None

    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    )
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'FloodWatch/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        rain_mm = data.get('rain', {}).get('1h', 0.0)
        weather = data.get('weather', [{}])[0]
        return {
            'rainfall_mm': float(rain_mm),
            'temperature_c': round(data['main']['temp'], 1),
            'humidity_pct': float(data['main']['humidity']),
            'description': weather.get('description', ''),
            'icon': weather.get('icon', ''),
        }
    except Exception as e:
        logger.error(f"Weather API error for ({lat},{lon}): {e}")
        return None


def simulate_weather_for_kerala(district):
    """
    Fallback: simulate realistic Kerala monsoon conditions when API key not set.
    Returns simulated weather dict.
    """
    import random, hashlib, time
    # Use district name + hour as seed for stable-but-rotating values
    hour = int(time.time() // 3600)
    seed = int(hashlib.md5(f"{district}{hour}".encode()).hexdigest(), 16) % 100000
    random.seed(seed)

    # Kerala monsoon probabilities
    rain_scenario = random.choices(
        ['none', 'light', 'moderate', 'heavy', 'very_heavy'],
        weights=[20, 30, 25, 15, 10]
    )[0]
    rain_map = {'none': 0.0, 'light': random.uniform(0.5, 3.0),
                'moderate': random.uniform(3.0, 15.0),
                'heavy': random.uniform(15.0, 35.0),
                'very_heavy': random.uniform(35.0, 80.0)}
    rain_mm = round(rain_map[rain_scenario], 1)
    desc_map = {'none': 'clear sky', 'light': 'light rain',
                'moderate': 'moderate rain', 'heavy': 'heavy rain',
                'very_heavy': 'thunderstorm with heavy rain'}
    humidity = random.randint(70, 98) if rain_mm > 0 else random.randint(55, 80)
    return {
        'rainfall_mm': rain_mm,
        'temperature_c': round(random.uniform(24.0, 33.0), 1),
        'humidity_pct': float(humidity),
        'description': desc_map[rain_scenario],
        'icon': '09d' if rain_mm > 0 else '01d',
        'simulated': True,
    }


def sync_all_water_levels():
    """
    Main sync function: fetch weather for each WaterLevel location,
    update water level based on rainfall, auto-generate alerts if needed.
    Returns summary dict.
    """
    from core.models import WaterLevel, FloodAlert

    updated = 0
    errors = 0
    alerts_created = 0
    now = timezone.now()

    for wl in WaterLevel.objects.all():
        try:
            # Fetch live or simulated weather
            weather = None
            if wl.latitude and wl.longitude:
                weather = fetch_weather(wl.latitude, wl.longitude)
            if not weather:
                weather = simulate_weather_for_kerala(wl.district)

            rain_mm = weather['rainfall_mm']
            accuracy = _rainfall_accuracy(rain_mm, weather['humidity_pct'], weather['description'])

            # Compute new water level
            old_level = wl.current_level_meters
            rise = rain_mm * RAIN_RISE_FACTOR
            # Apply natural drain if no rain
            drain = EVAPORATION_RATE if rain_mm == 0 else 0
            new_level = max(0.0, old_level + rise - drain)
            # Cap at danger + 20%
            new_level = min(new_level, wl.danger_level_meters * 1.2)
            new_level = round(new_level, 3)

            wl.current_level_meters = new_level
            wl.rainfall_mm = rain_mm
            wl.temperature_c = weather['temperature_c']
            wl.humidity_pct = weather['humidity_pct']
            wl.weather_description = weather['description']
            wl.weather_icon = weather.get('icon', '')
            wl.rainfall_accuracy_pct = accuracy
            wl.api_last_synced = now
            wl.save()  # triggers status auto-compute

            # Auto-generate alert if status is DANGER or CRITICAL
            if wl.status in ('DANGER', 'CRITICAL'):
                # Avoid duplicate alerts in last 6 hours
                recent = FloodAlert.objects.filter(
                    district=wl.district,
                    auto_generated=True,
                    issued_at__gte=now - timezone.timedelta(hours=6),
                    water_level=wl,
                ).exists()
                if not recent:
                    severity = 'EXTREME' if wl.status == 'CRITICAL' else 'HIGH'
                    FloodAlert.objects.create(
                        title=f"⚠️ Auto Alert: {wl.location_name} {wl.status}",
                        description=(
                            f"{wl.location_name} in {wl.district} has reached {wl.status} level "
                            f"({new_level:.2f}m / danger {wl.danger_level_meters}m). "
                            f"Rainfall: {rain_mm} mm/hr. Weather: {weather['description']}. "
                            f"Accuracy: {accuracy}%."
                        ),
                        affected_area=wl.location_name,
                        district=wl.district,
                        severity=severity,
                        water_level=wl,
                        auto_generated=True,
                        is_active=True,
                    )
                    alerts_created += 1

            updated += 1
        except Exception as e:
            logger.error(f"Error syncing {wl.location_name}: {e}")
            errors += 1

    return {'updated': updated, 'errors': errors, 'alerts_created': alerts_created}
