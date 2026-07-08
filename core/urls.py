from django.urls import path
from . import views

urlpatterns = [
    # Portal / landing
    path('portal/', views.portal_view, name='portal'),

    # Dashboard
    path('', views.home, name='home'),

    # Flood info
    path('alerts/', views.alerts_view, name='alerts'),
    path('water-levels/', views.water_levels_view, name='water_levels'),
    path('flood-map/', views.flood_map_view, name='flood_map'),
    path('rescue-teams/', views.rescue_teams_view, name='rescue_teams'),
    path('control-rooms/', views.control_rooms_view, name='control_rooms'),

    # Shelter Management
    path('shelters/', views.shelters_view, name='shelters'),
    path('shelters/add/', views.shelter_add, name='shelter_add'),
    path('shelters/<int:pk>/', views.shelter_detail, name='shelter_detail'),
    path('shelters/<int:pk>/checkin/', views.shelter_checkin, name='shelter_checkin'),
    path('shelters/<int:shelter_pk>/checkout/<int:person_pk>/', views.shelter_checkout, name='shelter_checkout'),
    path('shelters/<int:pk>/assign-team/', views.shelter_assign_team, name='shelter_assign_team'),
    path('api/shelters/', views.api_shelter_status, name='api_shelter_status'),

    # Reports
    path('report/', views.report_flood, name='report_flood'),
    path('report/success/<int:pk>/', views.report_success, name='report_success'),
    path('my-reports/', views.my_reports, name='my_reports'),
    path('admin-reports/', views.admin_reports_view, name='admin_reports'),
    path('admin-reports/action/<int:pk>/', views.admin_report_action, name='admin_report_action'),

    # API endpoints
    path('api/water-levels/', views.api_water_levels, name='api_water_levels'),
    path('api/weather-status/', views.api_weather_status, name='api_weather_status'),
    path('api/public-alerts/', views.api_public_alerts, name='api_public_alerts'),
    path('api/district-status/', views.api_district_status, name='api_district_status'),

    # Admin features
    path('admin/whatsapp-broadcast/', views.admin_whatsapp_broadcast, name='admin_whatsapp_broadcast'),
    path('admin/send-email-alerts/', views.admin_send_email_alerts, name='admin_send_email_alerts'),
    path('admin/district-pdf/<str:district>/', views.admin_district_pdf, name='admin_district_pdf'),

    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
]
