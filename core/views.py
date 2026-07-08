from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import WaterLevel, FloodAlert, FloodReport, RescueTeam, EmergencyContact, EmergencyShelter, DisplacedPerson
from .forms import FloodReportForm, LoginForm


# ─── Portal / Landing Page ────────────────────────────────────────────────────

def portal_view(request):
    """Public landing page — choose user or admin portal."""
    if request.user.is_authenticated:
        return redirect('admin_reports' if request.user.is_staff else 'home')
    stats = {
        'active_alerts': FloodAlert.objects.filter(is_active=True).count(),
        'critical_zones': WaterLevel.objects.filter(status__in=['DANGER', 'CRITICAL']).count(),
        'reports_today': FloodReport.objects.filter(reported_at__date=timezone.now().date()).count(),
        'rescue_teams': RescueTeam.objects.filter(is_available=True).count(),
    }
    return render(request, 'core/portal.html', stats)


# ─── Dashboard (Home) ─────────────────────────────────────────────────────────

@login_required
def home(request):
    alerts = FloodAlert.objects.filter(is_active=True).order_by('-issued_at')[:5]
    water_levels = WaterLevel.objects.all().order_by('-last_updated')[:8]
    recent_reports = FloodReport.objects.filter(status__in=['PENDING', 'VERIFIED']).order_by('-reported_at')[:6]
    rescue_teams = RescueTeam.objects.filter(is_available=True)[:6]

    stats = {
        'active_alerts': FloodAlert.objects.filter(is_active=True).count(),
        'critical_zones': WaterLevel.objects.filter(status__in=['DANGER', 'CRITICAL']).count(),
        'reports_today': FloodReport.objects.filter(reported_at__date=timezone.now().date()).count(),
        'rescue_teams': RescueTeam.objects.filter(is_available=True).count(),
    }

    context = {
        'alerts': alerts,
        'water_levels': water_levels,
        'recent_reports': recent_reports,
        'rescue_teams': rescue_teams,
        'stats': stats,
        'page': 'home',
    }
    return render(request, 'core/home.html', context)


# ─── Alerts ──────────────────────────────────────────────────────────────────

@login_required
def alerts_view(request):
    severity = request.GET.get('severity', '')
    district = request.GET.get('district', '')
    alerts = FloodAlert.objects.all()
    if severity:
        alerts = alerts.filter(severity=severity)
    if district:
        alerts = alerts.filter(district__icontains=district)
    districts = FloodAlert.objects.values_list('district', flat=True).distinct()
    return render(request, 'core/alerts.html', {
        'alerts': alerts, 'districts': districts,
        'selected_severity': severity, 'selected_district': district, 'page': 'alerts'
    })


# ─── Water Levels ────────────────────────────────────────────────────────────

@login_required
def water_levels_view(request):
    levels = WaterLevel.objects.all().order_by('district', 'location_name')
    status_filter = request.GET.get('status', '')
    if status_filter:
        levels = levels.filter(status=status_filter)
    return render(request, 'core/water_levels.html', {
        'levels': levels, 'status_filter': status_filter, 'page': 'water_levels'
    })


@login_required
def flood_map_view(request):
    return render(request, 'core/flood_map.html', {'page': 'flood_map'})


# ─── Report Flood ─────────────────────────────────────────────────────────────

@login_required
def report_flood(request):
    if request.method == 'POST':
        form = FloodReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save()
            messages.success(request, f'✅ Flood report submitted! Report ID: #{report.id}.')
            return redirect('report_success', pk=report.pk)
        else:
            messages.error(request, 'Please fix the errors below and resubmit.')
    else:
        form = FloodReportForm()
    return render(request, 'core/report_flood.html', {'form': form, 'page': 'report'})


def report_success(request, pk):
    report = get_object_or_404(FloodReport, pk=pk)
    return render(request, 'core/report_success.html', {'report': report})


# ─── Rescue Teams ─────────────────────────────────────────────────────────────

@login_required
def rescue_teams_view(request):
    district = request.GET.get('district', '')
    team_type = request.GET.get('type', '')
    teams = RescueTeam.objects.all()
    if district:
        teams = teams.filter(district__icontains=district)
    if team_type:
        teams = teams.filter(team_type=team_type)
    emergency_contacts = EmergencyContact.objects.filter(is_active=True)
    districts = RescueTeam.objects.values_list('district', flat=True).distinct()
    return render(request, 'core/rescue_teams.html', {
        'teams': teams,
        'emergency_contacts': emergency_contacts,
        'districts': districts,
        'selected_district': district,
        'selected_type': team_type,
        'team_types': RescueTeam._meta.get_field('team_type').choices,
        'page': 'rescue',
    })


# ─── Control Rooms ────────────────────────────────────────────────────────────

@login_required
def control_rooms_view(request):
    return render(request, 'core/control_rooms.html', {'page': 'control_rooms'})


# ─── My Reports ──────────────────────────────────────────────────────────────

@login_required
def my_reports(request):
    phone = request.GET.get('phone', '')
    reports = []
    if phone:
        reports = FloodReport.objects.filter(reporter_phone=phone).order_by('-reported_at')
    return render(request, 'core/my_reports.html', {'reports': reports, 'phone': phone, 'page': 'my_reports'})


# ─── Admin Reports ────────────────────────────────────────────────────────────

def admin_reports_view(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, 'You need admin access to view this page.')
        return redirect('login')

    filter_status = request.GET.get('status', '')
    filter_district = request.GET.get('district', '')
    filter_severity = request.GET.get('severity', '')
    filter_evacuation = request.GET.get('evacuation', '')

    reports = FloodReport.objects.all().select_related('rescue_team_assigned', 'reviewed_by')
    if filter_status:
        reports = reports.filter(status=filter_status)
    if filter_district:
        reports = reports.filter(district=filter_district)
    if filter_severity:
        reports = reports.filter(severity=filter_severity)
    if filter_evacuation == 'yes':
        reports = reports.filter(evacuation_needed=True)
    reports = reports.order_by('-reported_at')

    stats = {
        'pending': FloodReport.objects.filter(status='PENDING').count(),
        'verified': FloodReport.objects.filter(status='VERIFIED').count(),
        'resolved': FloodReport.objects.filter(status='RESOLVED').count(),
        'rejected': FloodReport.objects.filter(status='REJECTED').count(),
        'evacuation': FloodReport.objects.filter(evacuation_needed=True, status__in=['PENDING', 'VERIFIED']).count(),
        'total': FloodReport.objects.count(),
    }

    districts = FloodReport.objects.values_list('district', flat=True).distinct().order_by('district')
    rescue_teams = RescueTeam.objects.all().order_by('district', 'name')
    water_overview = WaterLevel.objects.all().order_by('-last_updated')[:12]

    return render(request, 'core/admin_reports.html', {
        'reports': reports,
        'stats': stats,
        'districts': districts,
        'rescue_teams': rescue_teams,
        'water_overview': water_overview,
        'filter_status': filter_status,
        'filter_district': filter_district,
        'filter_severity': filter_severity,
        'filter_evacuation': filter_evacuation,
        'page': 'admin_reports',
    })


def admin_report_action(request, pk):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('login')
    report = get_object_or_404(FloodReport, pk=pk)
    if request.method == 'POST':
        quick = request.POST.get('quick_action', '')
        if quick == 'verify':
            report.status = 'VERIFIED'
        elif quick == 'reject':
            report.status = 'REJECTED'
        elif quick == 'resolve':
            report.status = 'RESOLVED'
        else:
            report.status = request.POST.get('status', report.status)

        rescue_team_id = request.POST.get('rescue_team', '')
        if rescue_team_id:
            try:
                report.rescue_team_assigned_id = int(rescue_team_id)
            except (ValueError, TypeError):
                pass
        else:
            report.rescue_team_assigned = None

        report.admin_notes = request.POST.get('admin_notes', '')
        report.reviewed_by = request.user
        report.save()
        messages.success(request, f'✅ Report #{pk} updated to {report.status}.')

    referer = request.META.get('HTTP_REFERER', '/admin-reports/')
    if '/admin-reports/' in referer:
        return redirect(referer)
    return redirect('admin_reports')


# ─── API Endpoints ────────────────────────────────────────────────────────────

def api_water_levels(request):
    """JSON endpoint: live water levels with weather data."""
    levels = WaterLevel.objects.all().values(
        'id', 'location_name', 'district',
        'current_level_meters', 'danger_level_meters', 'warning_level_meters',
        'status', 'last_updated',
        'rainfall_mm', 'temperature_c', 'humidity_pct',
        'weather_description', 'rainfall_accuracy_pct', 'weather_icon',
        'api_last_synced',
    )
    data = []
    for lvl in levels:
        lvl['percentage'] = int((lvl['current_level_meters'] / lvl['danger_level_meters']) * 100) \
            if lvl['danger_level_meters'] else 0
        lvl['last_updated'] = lvl['last_updated'].strftime('%d %b %Y, %I:%M %p') if lvl['last_updated'] else ''
        lvl['api_last_synced'] = lvl['api_last_synced'].strftime('%d %b %Y, %I:%M %p') if lvl['api_last_synced'] else 'Never'
        data.append(lvl)
    return JsonResponse({'levels': data, 'count': len(data), 'timestamp': timezone.now().isoformat()})


def api_weather_status(request):
    """JSON endpoint: summary of current weather conditions for admin."""
    levels = WaterLevel.objects.all()
    summary = {
        'total': levels.count(),
        'critical': levels.filter(status='CRITICAL').count(),
        'danger': levels.filter(status='DANGER').count(),
        'warning': levels.filter(status='WARNING').count(),
        'watch': levels.filter(status='WATCH').count(),
        'normal': levels.filter(status='NORMAL').count(),
        'avg_rainfall_mm': 0,
        'max_rainfall_mm': 0,
        'active_alerts': FloodAlert.objects.filter(is_active=True).count(),
        'timestamp': timezone.now().isoformat(),
    }
    if levels.exists():
        rainfalls = [l.rainfall_mm for l in levels]
        summary['avg_rainfall_mm'] = round(sum(rainfalls) / len(rainfalls), 1)
        summary['max_rainfall_mm'] = round(max(rainfalls), 1)
    return JsonResponse(summary)


# ─── Auth ─────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('admin_reports' if request.user.is_staff else 'home')
    next_url = request.GET.get('next', '')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'],
                                password=form.cleaned_data['password'])
            if user:
                login(request, user)
                if next_url:
                    return redirect(next_url)
                if user.is_staff:
                    messages.success(request, f'👋 Welcome back, Admin {user.username}!')
                    return redirect('admin_reports')
                else:
                    messages.success(request, f'👋 Welcome, {user.username}!')
                    return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('portal')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()

        from django.contrib.auth.models import User as AuthUser
        form_data = {'username': username, 'first_name': first_name,
                     'last_name': last_name, 'email': email}

        if not username:
            messages.error(request, 'Username is required.')
            return render(request, 'core/register.html', {'form_data': form_data})
        if len(username) < 3:
            messages.error(request, 'Username must be at least 3 characters.')
            return render(request, 'core/register.html', {'form_data': form_data})
        if AuthUser.objects.filter(username=username).exists():
            messages.error(request, 'That username is already taken.')
            return render(request, 'core/register.html', {'form_data': form_data})
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'core/register.html', {'form_data': form_data})
        if len(password1) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
            return render(request, 'core/register.html', {'form_data': form_data})

        user = AuthUser.objects.create_user(
            username=username, password=password1,
            first_name=first_name, last_name=last_name, email=email,
        )
        login(request, user)
        messages.success(request, f'🎉 Welcome to FloodWatch Kerala, {username}!')
        return redirect('home')

    return render(request, 'core/register.html', {})


# ─── Public Alert API (no login required) ─────────────────────────────────────

def api_public_alerts(request):
    """
    Public JSON endpoint — no login required.
    Returns active HIGH and EXTREME alerts for real-time polling.
    Called every 15 seconds by the frontend alert system.
    """
    extreme = FloodAlert.objects.filter(is_active=True, severity='EXTREME').order_by('-issued_at')[:5]
    high    = FloodAlert.objects.filter(is_active=True, severity='HIGH').order_by('-issued_at')[:5]

    alert_level = None
    if extreme.exists():
        alert_level = 'EXTREME'
    elif high.exists():
        alert_level = 'HIGH'

    def fmt(a):
        return {
            'id':           a.id,
            'title':        a.title,
            'affected_area': a.affected_area,
            'district':     a.district,
            'severity':     a.severity,
            'issued_at':    a.issued_at.strftime('%d %b %Y, %I:%M %p'),
            'description':  a.description[:200],
        }

    return JsonResponse({
        'alert_level':    alert_level,
        'extreme_alerts': [fmt(a) for a in extreme],
        'high_alerts':    [fmt(a) for a in high],
        'total_active':   FloodAlert.objects.filter(is_active=True).count(),
        'timestamp':      timezone.now().isoformat(),
    })


# ─── Admin WhatsApp Broadcast ──────────────────────────────────────────────────

@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def admin_whatsapp_broadcast(request):
    """
    Returns a pre-built WhatsApp broadcast message with all active alerts.
    Called from Admin Reports page — opens WhatsApp Web with ready message.
    """
    active_alerts = FloodAlert.objects.filter(is_active=True).order_by('-issued_at')[:10]
    critical_zones = WaterLevel.objects.filter(status__in=['CRITICAL', 'DANGER']).order_by('district')

    lines = ["🚨 *FloodWatch Kerala — Official Alert Broadcast*",
             f"📅 {timezone.now().strftime('%d %b %Y, %I:%M %p IST')}", ""]

    if active_alerts.exists():
        lines.append("⚠️ *ACTIVE FLOOD ALERTS:*")
        for a in active_alerts:
            emoji = "🔴" if a.severity == 'EXTREME' else "🟠" if a.severity == 'HIGH' else "🟡"
            lines.append(f"{emoji} [{a.severity}] {a.title}")
            lines.append(f"   📍 {a.affected_area}, {a.district}")
    else:
        lines.append("✅ No active flood alerts at this time.")

    if critical_zones.exists():
        lines.append("")
        lines.append("🌊 *CRITICAL WATER LEVELS:*")
        for z in critical_zones:
            lines.append(f"• {z.location_name}, {z.district} — {z.status} ({z.current_level_meters}m)")

    lines += ["", "📞 Emergency: 1077", "🌐 Live updates: your-domain.com/alerts/",
              "", "_FloodWatch Kerala SDMA Portal_"]

    message = "\n".join(lines)
    import json
    return JsonResponse({'message': message, 'alert_count': active_alerts.count()})


# ─── Auto Email Alerts ─────────────────────────────────────────────────────────

@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def admin_send_email_alerts(request):
    """
    Sends flood alert emails to all registered users who have an email address.
    Admin-triggered from the Admin Reports page.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from django.contrib.auth.models import User as AuthUser
    from django.core.mail import send_mass_mail
    from django.conf import settings

    active_alerts = FloodAlert.objects.filter(is_active=True).order_by('-severity', '-issued_at')
    if not active_alerts.exists():
        return JsonResponse({'success': False, 'message': 'No active alerts to send.'})

    users_with_email = AuthUser.objects.filter(email__isnull=False).exclude(email='')
    if not users_with_email.exists():
        return JsonResponse({'success': False, 'message': 'No registered users with email addresses.'})

    # Build email content
    alert_lines = []
    for a in active_alerts[:10]:
        alert_lines.append(f"• [{a.severity}] {a.title}")
        alert_lines.append(f"  Location: {a.affected_area}, {a.district}")
        alert_lines.append(f"  Issued: {a.issued_at.strftime('%d %b %Y, %I:%M %p')}")
        alert_lines.append("")

    subject = f"🚨 FloodWatch Kerala — {'RED ALERT' if active_alerts.filter(severity='EXTREME').exists() else 'Flood Alert'} — {timezone.now().strftime('%d %b %Y')}"

    body = f"""FloodWatch Kerala — Official Flood Alert
{'='*50}

This is an automated alert from FloodWatch Kerala SDMA Portal.

ACTIVE FLOOD ALERTS ({active_alerts.count()} total):
{chr(10).join(alert_lines)}

WHAT TO DO:
• Follow instructions from local authorities
• Move to higher ground if in low-lying areas
• Call Emergency Helpline: 1077

View live updates: [your-domain]/alerts/

---
FloodWatch Kerala | Kerala State Disaster Management Authority
This is an automated message. Do not reply to this email.
"""

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'floodwatch@example.com')
    emails = [
        (subject, body, from_email, [u.email])
        for u in users_with_email
    ]

    try:
        sent = send_mass_mail(emails, fail_silently=False)
        return JsonResponse({'success': True, 'message': f'Alert sent to {sent} users.', 'count': sent})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Email error: {str(e)}'})


# ─── Admin PDF District Report ─────────────────────────────────────────────────

@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def admin_district_pdf(request, district):
    """
    Generates a professional PDF report for a specific district.
    Requires admin re-authentication via ADMIN_PDF_PASSWORD in settings.
    Includes: water levels, active alerts, flood reports, rescue teams.
    """
    from django.http import HttpResponse
    import io
    from django.conf import settings as dj_settings

    # ── PDF Password Gate ──────────────────────────────────────────────────────
    PDF_PASSWORD = getattr(dj_settings, 'ADMIN_PDF_PASSWORD', 'floodwatch2024')
    if request.method == 'GET':
        # Show password entry form
        return render(request, 'core/pdf_password.html', {'district': district})
    elif request.method == 'POST':
        entered = request.POST.get('pdf_password', '')
        if entered != PDF_PASSWORD:
            from django.contrib import messages as dj_messages
            dj_messages.error(request, '❌ Incorrect PDF password. Access denied.')
            return render(request, 'core/pdf_password.html', {'district': district, 'error': True})
    # Password verified — generate PDF

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    except ImportError:
        return HttpResponse("reportlab not installed. Run: pip install reportlab", status=500)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm,
                            leftMargin=2*cm, rightMargin=2*cm)

    styles = getSampleStyleSheet()
    # Custom styles
    title_style = ParagraphStyle('FWTitle', parent=styles['Title'],
        fontSize=20, fontName='Helvetica-Bold', textColor=colors.HexColor('#0369a1'),
        spaceAfter=4, alignment=TA_CENTER)
    sub_style = ParagraphStyle('FWSub', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor('#64748b'), alignment=TA_CENTER, spaceAfter=2)
    heading_style = ParagraphStyle('FWH2', parent=styles['Heading2'],
        fontSize=13, fontName='Helvetica-Bold', textColor=colors.HexColor('#0f172a'),
        spaceBefore=14, spaceAfter=6, borderPad=4)
    body_style = ParagraphStyle('FWBody', parent=styles['Normal'],
        fontSize=9, textColor=colors.HexColor('#334155'), spaceAfter=3)
    danger_style = ParagraphStyle('FWDanger', parent=body_style,
        textColor=colors.HexColor('#dc2626'), fontName='Helvetica-Bold')
    safe_style   = ParagraphStyle('FWSafe', parent=body_style,
        textColor=colors.HexColor('#16a34a'), fontName='Helvetica-Bold')

    story = []

    # Header
    story.append(Paragraph("FloodWatch Kerala", title_style))
    story.append(Paragraph(f"District Flood Status Report — {district}", sub_style))
    story.append(Paragraph(f"Generated: {timezone.now().strftime('%d %B %Y, %I:%M %p IST')} | Kerala SDMA Portal", sub_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0369a1'), spaceAfter=12))

    # Water Levels
    story.append(Paragraph("🌊 Water Level Monitoring Stations", heading_style))
    wls = WaterLevel.objects.filter(district__icontains=district).order_by('-last_updated')
    if wls.exists():
        wl_data = [['Station', 'Current (m)', 'Danger (m)', 'Status', 'Rainfall', 'Updated']]
        for w in wls:
            pct = int((w.current_level_meters/w.danger_level_meters*100)) if w.danger_level_meters else 0
            wl_data.append([
                w.location_name,
                f"{w.current_level_meters}m ({pct}%)",
                f"{w.danger_level_meters}m",
                w.status,
                f"{w.rainfall_mm}mm",
                w.last_updated.strftime('%d %b, %H:%M'),
            ])
        STATUS_COLORS_RL = {
            'CRITICAL': colors.HexColor('#7c3aed'),
            'DANGER':   colors.HexColor('#dc2626'),
            'WARNING':  colors.HexColor('#ea580c'),
            'WATCH':    colors.HexColor('#ca8a04'),
            'NORMAL':   colors.HexColor('#16a34a'),
        }
        ts = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0369a1')),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0,0), (-1,-1), 8),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f8fafc'), colors.white]),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ])
        for i, row in enumerate(wl_data[1:], 1):
            status = row[3]
            c = STATUS_COLORS_RL.get(status, colors.HexColor('#16a34a'))
            ts.add('TEXTCOLOR', (3,i), (3,i), c)
            ts.add('FONTNAME', (3,i), (3,i), 'Helvetica-Bold')
        t = Table(wl_data, colWidths=[4*cm, 2.5*cm, 2.5*cm, 2*cm, 2*cm, 2.5*cm])
        t.setStyle(ts)
        story.append(t)
    else:
        story.append(Paragraph("No monitoring stations found for this district.", body_style))
    story.append(Spacer(1, 8))

    # Active Alerts
    story.append(Paragraph("🚨 Active Flood Alerts", heading_style))
    alerts = FloodAlert.objects.filter(district__icontains=district, is_active=True).order_by('-issued_at')
    if alerts.exists():
        for a in alerts:
            sty = danger_style if a.severity in ['EXTREME','HIGH'] else body_style
            story.append(Paragraph(f"[{a.severity}] {a.title}", sty))
            story.append(Paragraph(f"Area: {a.affected_area} | Issued: {a.issued_at.strftime('%d %b %Y, %I:%M %p')}", body_style))
            story.append(Paragraph(a.description[:400], body_style))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("✅ No active alerts for this district.", safe_style))
    story.append(Spacer(1, 8))

    # Flood Reports
    story.append(Paragraph("📋 Flood Reports", heading_style))
    reports = FloodReport.objects.filter(district__icontains=district).order_by('-reported_at')[:15]
    if reports.exists():
        rep_data = [['Reporter', 'Location', 'Severity', 'Status', 'People Affected', 'Date']]
        for r in reports:
            rep_data.append([
                r.reporter_name, r.location[:30], r.severity, r.status,
                str(r.people_affected) if r.people_affected else '—',
                r.reported_at.strftime('%d %b %Y'),
            ])
        rt = Table(rep_data, colWidths=[3*cm, 3.5*cm, 2*cm, 2*cm, 2.5*cm, 2.5*cm])
        rt.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0,0), (-1,-1), 8),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f8fafc'), colors.white]),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(rt)
    else:
        story.append(Paragraph("No flood reports found for this district.", body_style))
    story.append(Spacer(1, 8))

    # Rescue Teams
    story.append(Paragraph("🚁 Rescue Teams", heading_style))
    teams = RescueTeam.objects.filter(district__icontains=district)
    if teams.exists():
        t_data = [['Team Name', 'Type', 'Contact', 'Personnel', 'Boats', 'Status']]
        for t in teams:
            t_data.append([
                t.name[:30], t.get_team_type_display()[:20],
                t.contact_number, str(t.personnel_count),
                str(t.boats_available),
                '✅ Available' if t.is_available else '❌ Busy',
            ])
        tt = Table(t_data, colWidths=[3*cm, 3.5*cm, 2.5*cm, 2*cm, 1.5*cm, 2.5*cm])
        tt.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#059669')),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0,0), (-1,-1), 8),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f0fdf4'), colors.white]),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(tt)
    else:
        story.append(Paragraph("No rescue teams registered for this district.", body_style))

    # Footer
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
    story.append(Paragraph(
        f"FloodWatch Kerala SDMA Portal | Confidential — Official Use Only | {timezone.now().strftime('%d %b %Y')}",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=7,
                       textColor=colors.HexColor('#94a3b8'), alignment=TA_CENTER, spaceBefore=8)
    ))

    doc.build(story)
    buf.seek(0)
    filename = f"FloodWatch_{district}_{timezone.now().strftime('%Y%m%d_%H%M')}.pdf"
    response = HttpResponse(buf.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ─── Admin SVG Map with Pulsing Districts API ──────────────────────────────────

def api_district_status(request):
    """
    Returns aggregated worst status per district for the SVG map.
    Used by admin map and public map.
    """
    KERALA_DISTRICTS = [
        'Kasaragod','Kannur','Wayanad','Kozhikode','Malappuram',
        'Palakkad','Thrissur','Ernakulam','Idukki','Kottayam',
        'Pathanamthitta','Alappuzha','Kollam','Thiruvananthapuram'
    ]
    STATUS_ORDER = ['CRITICAL','DANGER','WARNING','WATCH','NORMAL']

    result = {}
    for d in KERALA_DISTRICTS:
        levels = WaterLevel.objects.filter(district__icontains=d)
        worst = 'NORMAL'
        if levels.exists():
            statuses = list(levels.values_list('status', flat=True))
            for s in STATUS_ORDER:
                if s in statuses:
                    worst = s
                    break
        alerts = FloodAlert.objects.filter(district__icontains=d, is_active=True)
        has_extreme = alerts.filter(severity='EXTREME').exists()
        has_high    = alerts.filter(severity='HIGH').exists()
        result[d] = {
            'status': worst,
            'has_active_alerts': alerts.exists(),
            'has_extreme': has_extreme,
            'has_high': has_high,
            'station_count': levels.count(),
            'max_rainfall': float(max(list(levels.values_list('rainfall_mm', flat=True)) or [0])),
        }

    return JsonResponse({'districts': result, 'timestamp': timezone.now().isoformat()})


# ─── Shelter Management ───────────────────────────────────────────────────────

from django.db.models import Sum

KERALA_DISTRICTS = [
    'Thiruvananthapuram', 'Kollam', 'Pathanamthitta', 'Alappuzha',
    'Kottayam', 'Idukki', 'Ernakulam', 'Thrissur', 'Palakkad',
    'Malappuram', 'Kozhikode', 'Wayanad', 'Kannur', 'Kasaragod',
]


@login_required
def shelters_view(request):
    district = request.GET.get('district', '')
    status = request.GET.get('status', '')
    shelters = EmergencyShelter.objects.prefetch_related('assigned_teams').all()
    if district:
        shelters = shelters.filter(district__icontains=district)
    if status:
        shelters = shelters.filter(status=status)

    totals = EmergencyShelter.objects.aggregate(
        total_capacity=Sum('total_capacity'),
        total_occupancy=Sum('current_occupancy'),
    )
    stats = {
        'total_shelters': EmergencyShelter.objects.count(),
        'open_shelters': EmergencyShelter.objects.filter(status='OPEN').count(),
        'full_shelters': EmergencyShelter.objects.filter(status='FULL').count(),
        'total_capacity': totals['total_capacity'] or 0,
        'total_occupancy': totals['total_occupancy'] or 0,
        'total_displaced': DisplacedPerson.objects.filter(checked_out_at__isnull=True).count(),
    }

    rescue_teams = RescueTeam.objects.filter(is_available=True).order_by('district', 'name')
    districts = EmergencyShelter.objects.values_list('district', flat=True).distinct()

    return render(request, 'core/shelters.html', {
        'shelters': shelters,
        'stats': stats,
        'rescue_teams': rescue_teams,
        'districts': districts,
        'kerala_districts': KERALA_DISTRICTS,
        'selected_district': district,
        'selected_status': status,
        'page': 'shelters',
    })


@login_required
def shelter_detail(request, pk):
    shelter = get_object_or_404(EmergencyShelter, pk=pk)
    persons = shelter.persons.filter(checked_out_at__isnull=True).order_by('-checked_in_at')
    all_teams = RescueTeam.objects.all().order_by('district', 'name')
    return render(request, 'core/shelter_detail.html', {
        'shelter': shelter,
        'persons': persons,
        'all_teams': all_teams,
        'page': 'shelters',
    })


@login_required
def shelter_checkin(request, pk):
    if request.method != 'POST':
        return redirect('shelter_detail', pk=pk)
    shelter = get_object_or_404(EmergencyShelter, pk=pk)
    if shelter.available_capacity() <= 0:
        messages.error(request, 'This shelter is at full capacity.')
        return redirect('shelter_detail', pk=pk)

    name = request.POST.get('name', '').strip()
    if not name:
        messages.error(request, 'Name is required.')
        return redirect('shelter_detail', pk=pk)

    family_size = max(1, int(request.POST.get('family_size', 1) or 1))

    person = DisplacedPerson.objects.create(
        shelter=shelter,
        name=name,
        age=request.POST.get('age') or None,
        gender=request.POST.get('gender', ''),
        phone=request.POST.get('phone', '').strip(),
        home_address=request.POST.get('home_address', '').strip(),
        home_district=request.POST.get('home_district', '').strip(),
        family_size=family_size,
        needs_medical=request.POST.get('needs_medical') == 'on',
        medical_notes=request.POST.get('medical_notes', '').strip(),
        notes=request.POST.get('notes', '').strip(),
        checked_in_by=request.user,
    )

    shelter.current_occupancy = shelter.current_occupancy + family_size
    shelter.save()
    messages.success(request, f'✅ {name} (family of {family_size}) checked in. Token #{person.id}')
    return redirect('shelter_detail', pk=pk)


@login_required
def shelter_checkout(request, shelter_pk, person_pk):
    shelter = get_object_or_404(EmergencyShelter, pk=shelter_pk)
    person = get_object_or_404(DisplacedPerson, pk=person_pk, shelter=shelter)
    if person.checked_out_at is None:
        person.checked_out_at = timezone.now()
        person.save()
        shelter.current_occupancy = max(0, shelter.current_occupancy - person.family_size)
        shelter.save()
        messages.success(request, f'✅ {person.name} checked out successfully.')
    return redirect('shelter_detail', pk=shelter_pk)


@login_required
def shelter_assign_team(request, pk):
    if request.method != 'POST':
        return redirect('shelter_detail', pk=pk)
    shelter = get_object_or_404(EmergencyShelter, pk=pk)
    team_id = request.POST.get('team_id')
    action = request.POST.get('action', 'assign')
    try:
        team = RescueTeam.objects.get(pk=team_id)
        if action == 'assign':
            shelter.assigned_teams.add(team)
            messages.success(request, f'✅ {team.name} assigned to {shelter.name}.')
        else:
            shelter.assigned_teams.remove(team)
            messages.success(request, f'Team removed from {shelter.name}.')
    except RescueTeam.DoesNotExist:
        messages.error(request, 'Team not found.')
    return redirect('shelter_detail', pk=pk)


@login_required
def shelter_add(request):
    if not request.user.is_staff:
        messages.error(request, 'Admin access required.')
        return redirect('shelters')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Shelter name required.')
            return redirect('shelters')
        EmergencyShelter.objects.create(
            name=name,
            shelter_type=request.POST.get('shelter_type', 'SCHOOL'),
            district=request.POST.get('district', ''),
            address=request.POST.get('address', '').strip(),
            total_capacity=int(request.POST.get('total_capacity', 100) or 100),
            contact_person=request.POST.get('contact_person', '').strip(),
            contact_phone=request.POST.get('contact_phone', '').strip(),
            has_medical=request.POST.get('has_medical') == 'on',
            has_food=request.POST.get('has_food') == 'on',
            has_water=request.POST.get('has_water') == 'on',
            has_power=request.POST.get('has_power') == 'on',
            has_toilets=request.POST.get('has_toilets') == 'on',
            notes=request.POST.get('notes', '').strip(),
        )
        messages.success(request, f'✅ Shelter "{name}" added successfully.')
    return redirect('shelters')


@login_required
def api_shelter_status(request):
    shelters = EmergencyShelter.objects.all()
    data = [{
        'id': s.id,
        'name': s.name,
        'district': s.district,
        'status': s.status,
        'total_capacity': s.total_capacity,
        'current_occupancy': s.current_occupancy,
        'available': s.available_capacity(),
        'occupancy_pct': s.occupancy_pct(),
        'lat': s.latitude,
        'lng': s.longitude,
    } for s in shelters]
    return JsonResponse({'shelters': data, 'count': len(data)})
