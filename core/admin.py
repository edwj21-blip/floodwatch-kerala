from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import WaterLevel, FloodAlert, FloodReport, RescueTeam, EmergencyContact


@admin.register(WaterLevel)
class WaterLevelAdmin(admin.ModelAdmin):
    list_display = ['location_name', 'district', 'level_bar', 'current_level_meters', 'danger_level_meters', 'status_badge', 'last_updated']
    list_filter = ['status', 'district']
    search_fields = ['location_name', 'district']
    readonly_fields = ['status', 'last_updated']
    fieldsets = (
        ('Location', {'fields': ('location_name', 'district', 'latitude', 'longitude')}),
        ('Water Levels', {'fields': ('current_level_meters', 'warning_level_meters', 'danger_level_meters')}),
        ('Status', {'fields': ('status', 'last_updated', 'notes')}),
    )

    def status_badge(self, obj):
        colors = {
            'NORMAL': '#22c55e',
            'WATCH': '#eab308',
            'WARNING': '#f97316',
            'DANGER': '#ef4444',
            'CRITICAL': '#7c3aed',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:bold;">{}</span>',
            color, obj.status
        )
    status_badge.short_description = 'Status'

    def level_bar(self, obj):
        pct = obj.get_percentage()
        if pct >= 100:
            color = '#7c3aed'
        elif pct >= 85:
            color = '#ef4444'
        elif pct >= 60:
            color = '#f97316'
        elif pct >= 40:
            color = '#eab308'
        else:
            color = '#22c55e'
        return format_html(
            '<div style="width:120px;background:#e5e7eb;border-radius:4px;height:14px;">'
            '<div style="width:{}%;background:{};height:14px;border-radius:4px;"></div>'
            '</div> {}%',
            pct, color, pct
        )
    level_bar.short_description = 'Level %'


@admin.register(FloodAlert)
class FloodAlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'district', 'severity_badge', 'affected_area', 'is_active', 'issued_at']
    list_filter = ['severity', 'is_active', 'district']
    search_fields = ['title', 'affected_area', 'district']
    list_editable = ['is_active']
    readonly_fields = ['issued_at']

    def severity_badge(self, obj):
        colors = {
            'LOW': '#22c55e',
            'MEDIUM': '#eab308',
            'HIGH': '#ef4444',
            'EXTREME': '#7c3aed',
        }
        color = colors.get(obj.severity, '#6b7280')
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:bold;">{}</span>',
            color, obj.severity
        )
    severity_badge.short_description = 'Severity'


@admin.register(FloodReport)
class FloodReportAdmin(admin.ModelAdmin):
    list_display = ['reporter_name', 'district', 'location', 'severity_badge', 'status', 'evacuation_needed', 'reported_at', 'photo_preview']
    list_filter = ['status', 'severity', 'district', 'evacuation_needed']
    search_fields = ['reporter_name', 'location', 'district', 'description']
    readonly_fields = ['reported_at', 'photo_preview']
    list_editable = ['status']
    fieldsets = (
        ('Reporter Info', {'fields': ('reporter_name', 'reporter_phone', 'reporter_email')}),
        ('Incident Details', {'fields': ('location', 'district', 'description', 'water_level_estimate', 'severity', 'people_affected', 'evacuation_needed')}),
        ('Evidence', {'fields': ('photo', 'photo_preview', 'latitude', 'longitude')}),
        ('Admin', {'fields': ('status', 'reviewed_by', 'rescue_team_assigned', 'admin_notes', 'reported_at')}),
    )

    def severity_badge(self, obj):
        colors = {'MINOR': '#22c55e', 'MODERATE': '#eab308', 'SEVERE': '#ef4444', 'CATASTROPHIC': '#7c3aed'}
        color = colors.get(obj.severity, '#6b7280')
        return format_html('<span style="background:{};color:white;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:bold;">{}</span>', color, obj.severity)
    severity_badge.short_description = 'Severity'

    def status_badge(self, obj):
        colors = {'PENDING': '#eab308', 'VERIFIED': '#3b82f6', 'RESOLVED': '#22c55e', 'REJECTED': '#6b7280'}
        color = colors.get(obj.status, '#6b7280')
        return format_html('<span style="background:{};color:white;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:bold;">{}</span>', color, obj.status)
    status_badge.short_description = 'Status'

    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="max-width:200px;max-height:150px;border-radius:8px;" />', obj.photo.url)
        return "No photo uploaded"
    photo_preview.short_description = 'Photo Preview'


@admin.register(RescueTeam)
class RescueTeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'team_type', 'district', 'contact_number', 'is_available', 'personnel_count', 'boats_available']
    list_filter = ['team_type', 'is_available', 'district']
    search_fields = ['name', 'district', 'contact_number']
    list_editable = ['is_available']


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'designation', 'department', 'phone', 'district', 'is_active']
    list_filter = ['district', 'is_active']
    search_fields = ['name', 'department', 'phone']
    list_editable = ['is_active']


from .models import EmergencyShelter, DisplacedPerson

@admin.register(EmergencyShelter)
class EmergencyShelterAdmin(admin.ModelAdmin):
    list_display = ('name', 'district', 'shelter_type', 'status', 'current_occupancy', 'total_capacity', 'contact_person')
    list_filter = ('district', 'status', 'shelter_type', 'has_medical')
    search_fields = ('name', 'district', 'address', 'contact_person')
    filter_horizontal = ('assigned_teams',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(DisplacedPerson)
class DisplacedPersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'shelter', 'family_size', 'home_district', 'checked_in_at', 'checked_out_at', 'needs_medical')
    list_filter = ('shelter__district', 'needs_medical', 'gender')
    search_fields = ('name', 'phone', 'home_address')
    readonly_fields = ('checked_in_at',)
