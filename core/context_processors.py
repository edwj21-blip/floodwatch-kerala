from .models import FloodAlert


def active_alert_notifications(request):
    """
    Injects active HIGH and EXTREME flood alerts into every template context.
    Used by the global alert sound + popup notification system in base.html.
    """
    try:
        high_alerts = FloodAlert.objects.filter(
            is_active=True, severity='HIGH'
        ).order_by('-issued_at')[:3]

        extreme_alerts = FloodAlert.objects.filter(
            is_active=True, severity='EXTREME'
        ).order_by('-issued_at')[:3]

        # Highest severity for triggering the right sound
        alert_level = None
        if extreme_alerts.exists():
            alert_level = 'EXTREME'
        elif high_alerts.exists():
            alert_level = 'HIGH'

        return {
            'notif_high_alerts': high_alerts,
            'notif_extreme_alerts': extreme_alerts,
            'notif_alert_level': alert_level,
            'active_alert_count': FloodAlert.objects.filter(is_active=True).count(),
        }
    except Exception:
        # Fail silently so DB migration errors don't crash the site
        return {
            'notif_high_alerts': [],
            'notif_extreme_alerts': [],
            'notif_alert_level': None,
            'active_alert_count': 0,
        }
