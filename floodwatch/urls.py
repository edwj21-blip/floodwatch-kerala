from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.staticfiles.views import serve as static_serve
from django.views.generic import RedirectView

admin.site.site_header = "FloodWatch Admin"
admin.site.site_title = "FloodWatch Admin Portal"
admin.site.index_title = "Flood Management Dashboard"

# Serve service worker from root (browser requires this exact path)
def serve_sw(request):
    from django.http import FileResponse, Http404
    import os
    sw_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'core', 'js', 'fw-sw.js')
    if not os.path.exists(sw_path):
        raise Http404
    response = FileResponse(open(sw_path, 'rb'), content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    return response

urlpatterns = [
    path('admin/', admin.site.urls),
    path('fw-sw.js', serve_sw, name='service_worker'),   # service worker at root
    path('', include('core.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
